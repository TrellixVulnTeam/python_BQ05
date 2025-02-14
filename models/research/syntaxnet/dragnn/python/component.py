# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Builds a DRAGNN graph for local training."""

from abc import ABCMeta
from abc import abstractmethod

import tensorflow as tf
from tensorflow.python.platform import tf_logging as logging

from dragnn.protos import export_pb2
from dragnn.python import dragnn_ops
from dragnn.python import network_units
from dragnn.python import runtime_support
from syntaxnet.util import check
from syntaxnet.util import registry


def build_softmax_cross_entropy_loss(logits, gold):
    """Builds softmax cross entropy loss."""

    # A gold label > -1 determines that the sentence is still
    # in a valid state. Otherwise, the sentence has ended.
    #
    # We add only the valid sentences to the loss, in the following way:
    #   1. We compute 'valid_ix', the indices in gold that contain
    #      valid oracle actions.
    #   2. We compute the cost function by comparing logits and gold
    #      only for the valid indices.
    valid = tf.greater(gold, -1)
    valid_ix = tf.reshape(tf.where(valid), [-1])
    valid_gold = tf.gather(gold, valid_ix)

    valid_logits = tf.gather(logits, valid_ix)
    cost = tf.reduce_sum(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=tf.cast(valid_gold, tf.int64),
            logits=valid_logits,
            name='sparse_softmax_cross_entropy_with_logits'))

    correct = tf.reduce_sum(
        tf.to_int32(tf.nn.in_top_k(valid_logits, valid_gold, 1)))
    total = tf.size(valid_gold)

    return cost, correct, total, valid_logits, valid_gold


def build_sigmoid_cross_entropy_loss(logits, gold, indices, probs):
    """Builds sigmoid cross entropy loss."""

    # Filter out entries where gold <= -1, which are batch padding entries.
    valid = tf.greater(gold, -1)
    valid_ix = tf.reshape(tf.where(valid), [-1])
    valid_gold = tf.gather(gold, valid_ix)
    valid_indices = tf.gather(indices, valid_ix)
    valid_probs = tf.gather(probs, valid_ix)

    # NB: tf.gather_nd() raises an error on CPU for out-of-bounds indices.  That's
    # why we need to filter out the gold=-1 batch padding above.
    valid_pairs = tf.stack([valid_indices, valid_gold], axis=1)
    valid_logits = tf.gather_nd(logits, valid_pairs)
    cost = tf.reduce_sum(
        tf.nn.sigmoid_cross_entropy_with_logits(
            labels=valid_probs,
            logits=valid_logits,
            name='sigmoid_cross_entropy_with_logits'))

    gold_bool = valid_probs > 0.5
    predicted_bool = valid_logits > 0.0
    total = tf.size(gold_bool)
    with tf.control_dependencies([
        tf.assert_equal(
            total, tf.size(predicted_bool), name='num_predicted_gold_mismatch')
    ]):
        agreement_bool = tf.logical_not(tf.logical_xor(gold_bool, predicted_bool))
    correct = tf.reduce_sum(tf.to_int32(agreement_bool))

    cost.set_shape([])
    correct.set_shape([])
    total.set_shape([])
    return cost, correct, total, gold


class NetworkState(object):
    """Simple utility to manage the state of a DRAGNN network.

    This class encapsulates the variables that are a specific to any
    particular instance of a DRAGNN stack, as constructed by the
    MasterBuilder below.

    Attributes:
      activations: Dictionary mapping layer names to StoredActivation objects.
    """

    def __init__(self):
        self.activations = {}


class MasterState(object):
    """Simple utility to encapsulate tensors associated with the master state.

    Attributes:
      handle: string tensor handle to the underlying ComputeSession.
      current_batch_size: int tensor containing the current batch size.
    """

    def __init__(self, handle, current_batch_size):
        self.handle = handle
        self.current_batch_size = current_batch_size


@registry.RegisteredClass
class ComponentBuilderBase(object):
    """Utility to build a single Component in a DRAGNN stack of models.

    This class handles converting a ComponentSpec proto into various TF
    sub-graphs. It will stitch together various neural units with dynamic
    unrolling inside a tf.while loop.

    All variables for parameters are created during the constructor within the
    scope of the component's name, e.g. 'tagger/embedding_matrix_0' for a
    component named 'tagger'.

    As part of the specification, ComponentBuilder will wrap an underlying
    NetworkUnit which generates the actual network layout.

    Attributes:
      master: dragnn.MasterBuilder that owns this component.
      num_actions: Number of actions in the transition system.
      name: Name of this component.
      spec: dragnn.ComponentSpec that configures this component.
      moving_average: True if moving-average parameters should be used.
    """

    __metaclass__ = ABCMeta  # required for @abstractmethod

    def __init__(self, master, component_spec, attr_defaults=None):
        """Initializes the ComponentBuilder from specifications.

        Args:
          master: dragnn.MasterBuilder object.
          component_spec: dragnn.ComponentSpec proto to be built.
          attr_defaults: Optional dict of component attribute defaults.  If not
              provided or if empty, attributes are not extracted.
        """
        self.master = master
        self.num_actions = component_spec.num_actions
        self.name = component_spec.name
        self.spec = component_spec
        self.moving_average = None

        # Determine if this component should apply self-normalization.
        self.eligible_for_self_norm = (
            not self.master.hyperparams.self_norm_components_filter or self.name in
            self.master.hyperparams.self_norm_components_filter.split(','))

        # Extract component attributes before make_network(), so the network unit
        # can access them.
        self._attrs = {}
        global_attr_defaults = {
            'locally_normalize': False,
            'output_as_probabilities': False
        }
        if attr_defaults:
            global_attr_defaults.update(attr_defaults)
        self._attrs = network_units.get_attrs_with_defaults(
            self.spec.component_builder.parameters, global_attr_defaults)
        do_local_norm = self._attrs['locally_normalize']
        self._output_as_probabilities = self._attrs['output_as_probabilities']
        with tf.variable_scope(self.name):
            self.training_beam_size = tf.constant(
                self.spec.training_beam_size, name='TrainingBeamSize')
            self.inference_beam_size = tf.constant(
                self.spec.inference_beam_size, name='InferenceBeamSize')
            self.locally_normalize = tf.constant(
                do_local_norm, name='LocallyNormalize')
            self._step = tf.get_variable(
                'step', [], initializer=tf.zeros_initializer(), dtype=tf.int32)
            self._total = tf.get_variable(
                'total', [], initializer=tf.zeros_initializer(), dtype=tf.int32)

        # Construct network variables.
        self.network = self.make_network(self.spec.network_unit)

        # Construct moving average.
        if self.master.hyperparams.use_moving_average:
            self.moving_average = tf.train.ExponentialMovingAverage(
                decay=self.master.hyperparams.average_weight, num_updates=self._step)
            self.avg_ops = [self.moving_average.apply(self.network.params)]

        # Used to export the cell; see add_cell_input() and add_cell_output().
        self._cell_subgraph_spec = export_pb2.CellSubgraphSpec()

    def make_network(self, network_unit):
        """Makes a NetworkUnitInterface object based on the network_unit spec.

        Components may override this method to exert control over the
        network unit construction, such as which network units are supported.

        Args:
          network_unit: RegisteredModuleSpec proto defining the network unit.

        Returns:
          An implementation of NetworkUnitInterface.

        Raises:
          ValueError: if the requested network unit is not found in the registry.
        """
        network_type = network_unit.registered_name

        with tf.variable_scope(self.name):
            # Raises ValueError if not found.
            return network_units.NetworkUnitInterface.Create(network_type, self)

    @abstractmethod
    def build_greedy_training(self, state, network_states):
        """Builds a training graph for this component.

        Two assumptions are made about the resulting graph:
        1. An oracle will be used to unroll the state and compute the cost.
        2. The graph will be differentiable when the cost is being minimized.

        Args:
          state: MasterState from the 'AdvanceMaster' op that advances the
            underlying master to this component.
          network_states: dictionary of component NetworkState objects.

        Returns:
          (state, cost, correct, total) -- These are TF ops corresponding to
          the final state after unrolling, the total cost, the total number of
          correctly predicted actions, and the total number of actions.
        """
        pass

    def build_structured_training(self, state, network_states):
        """Builds a beam search based training loop for this component.

        The default implementation builds a dummy graph and raises a
        TensorFlow runtime exception to indicate that structured training
        is not implemented.

        Args:
          state: MasterState from the 'AdvanceMaster' op that advances the
            underlying master to this component.
          network_states: dictionary of component NetworkState objects.

        Returns:
          (handle, cost, correct, total) -- These are TF ops corresponding
          to the final handle after unrolling, the total cost, and the
          total number of actions. Since the number of correctly predicted
          actions is not applicable in the structured training setting, a
          dummy value should returned.
        """
        del network_states  # Unused.
        with tf.control_dependencies([tf.Assert(False, ['Not implemented.'])]):
            handle = tf.identity(state.handle)
        cost = tf.constant(0.)
        correct, total = tf.constant(0), tf.constant(0)
        return handle, cost, correct, total

    @abstractmethod
    def build_greedy_inference(self, state, network_states,
                               during_training=False):
        """Builds an inference graph for this component.

        If this graph is being constructed 'during_training', then it needs to be
        differentiable even though it doesn't return an explicit cost.

        There may be other cases where the distinction between training and eval is
        important. The handling of dropout is an example of this.

        Args:
          state: MasterState from the 'AdvanceMaster' op that advances the
            underlying master to this component.
          network_states: dictionary of component NetworkState objects.
          during_training: whether the graph is being constructed during training

        Returns:
          Handle to the state once inference is complete for this Component.
        """
        pass

    def get_summaries(self):
        """Constructs a set of summaries for this component.

        Returns:
          List of Summary ops to get parameter norms, progress reports, and
          so forth for this component.
        """

        def combine_norm(matrices):
            # Handles None in cases where the optimizer or moving average slot is
            # not present.
            squares = [tf.reduce_sum(tf.square(m)) for m in matrices if m is not None]

            # Some components may not have any parameters, in which case we simply
            # return zero.
            if squares:
                return tf.sqrt(tf.add_n(squares))
            else:
                return tf.constant(0, tf.float32)

        summaries = []
        summaries.append(tf.summary.scalar('%s step' % self.name, self._step))
        summaries.append(tf.summary.scalar('%s total' % self.name, self._total))
        if self.network.params:
            summaries.append(
                tf.summary.scalar('%s parameter Norm' % self.name,
                                  combine_norm(self.network.params)))
            slot_names = self.master.optimizer.get_slot_names()
            for name in slot_names:
                slot_params = [
                    self.master.optimizer.get_slot(p, name) for p in self.network.params
                ]
                summaries.append(
                    tf.summary.scalar('%s %s Norm' % (self.name, name),
                                      combine_norm(slot_params)))

            # Construct moving average.
            if self.master.hyperparams.use_moving_average:
                summaries.append(
                    tf.summary.scalar('%s avg Norm' % self.name,
                                      combine_norm([
                                          self.moving_average.average(p)
                                          for p in self.network.params
                                      ])))

        return summaries

    def get_variable(self, var_name=None, var_params=None):
        """Returns either the original or averaged version of a given variable.

        If the master.read_from_avg flag is set to True, and the
        ExponentialMovingAverage (EMA) object has been attached, then this will ask
        the EMA object for the given variable.

        This is to allow executing inference from the averaged version of
        parameters.

        Arguments:
          var_name: Name of the variable.
          var_params: tf.Variable for which to retrieve an average.

        Only one of |var_name| or |var_params| needs to be provided.  If both are
        provided, |var_params| takes precedence.

        Returns:
          tf.Variable object corresponding to original or averaged version.
        """
        if var_params is not None:
            var_name = var_params.name
        else:
            check.NotNone(var_name, 'specify at least one of var_name or var_params')
            var_params = tf.get_variable(var_name)

        if self.moving_average and self.master.read_from_avg:
            logging.info('Retrieving average for: %s', var_name)
            var_params = self.moving_average.average(var_params)
            assert var_params
        logging.info('Returning: %s', var_params.name)
        return var_params

    def advance_counters(self, total):
        """Returns ops to advance the per-component step and total counters.

        Args:
          total: Total number of actions to increment counters by.

        Returns:
          tf.Group op incrementing 'step' by 1 and 'total' by total.
        """
        update_total = tf.assign_add(self._total, total, use_locking=True)
        update_step = tf.assign_add(self._step, 1, use_locking=True)
        return tf.group(update_total, update_step)

    def add_regularizer(self, cost):
        """Adds L2 regularization for parameters which have it turned on.

        Args:
          cost: float cost before regularization.

        Returns:
          Updated cost optionally including regularization.
        """
        if self.network is None:
            return cost
        regularized_weights = self.network.get_l2_regularized_weights()
        if not regularized_weights:
            return cost
        l2_coeff = self.master.hyperparams.l2_regularization_coefficient
        if l2_coeff == 0.0:
            return cost
        tf.logging.info('[%s] Regularizing parameters: %s', self.name,
                        [w.name for w in regularized_weights])
        l2_costs = [tf.nn.l2_loss(p) for p in regularized_weights]
        return tf.add(cost, l2_coeff * tf.add_n(l2_costs), name='regularizer')

    def build_post_restore_hook(self):
        """Builds a post restore graph for this component.

        This is a run-once graph that prepares any state necessary for the
        inference portion of the component. It is generally a no-op.

        Returns:
          A no-op state.
        """
        logging.info('Building default post restore hook for component: %s',
                     self.spec.name)
        return tf.no_op(name='setup_%s' % self.spec.name)

    def attr(self, name):
        """Returns the value of the component attribute with the |name|."""
        return self._attrs[name]

    def has_attr(self, name):
        """Checks whether a component attribute with the given |name| exists.

        Arguments:
           name: attribute name

        Returns:
          'true' if the name exists and 'false' otherwise.
        """
        return name in self._attrs

    def _add_runtime_hooks(self):
        """Adds "hook" nodes to the graph for use by the runtime, if enabled.

        Does nothing if master.build_runtime_graph is False.  Subclasses should call
        this at the end of build_*_inference().  For details on the runtime hooks,
        see runtime_support.py.
        """
        if self.master.build_runtime_graph:
            with tf.variable_scope(self.name, reuse=True):
                runtime_support.add_hooks(self, self._cell_subgraph_spec)
            self._cell_subgraph_spec = None  # prevent further exports

    def add_cell_input(self, dtype, shape, name, input_type='TYPE_FEATURE'):
        """Adds an input to the current CellSubgraphSpec.

        Creates a tf.placeholder() with the given |dtype| and |shape|, adds it as a
        cell input with the |name| and |input_type|, and returns the placeholder to
        be used in place of the actual input tensor.

        Args:
          dtype: DType of the cell input.
          shape: Static shape of the cell input.
          name: Logical name of the cell input.
          input_type: Name of the appropriate CellSubgraphSpec.Input.Type enum.

        Returns:
          A tensor to use in place of the actual input tensor.

        Raises:
          TypeError: If the |shape| is the wrong type.
          RuntimeError: If the cell has already been exported.
        """
        if not (isinstance(shape, list) and
                all(isinstance(dim, int) for dim in shape)):
            raise TypeError('shape must be a list of int')
        if not self._cell_subgraph_spec:
            raise RuntimeError('already exported a CellSubgraphSpec')

        with tf.name_scope(None):
            tensor = tf.placeholder(
                dtype, shape, name='{}/INPUT/{}'.format(self.name, name))
        self._cell_subgraph_spec.input.add(
            name=name,
            tensor=tensor.name,
            type=export_pb2.CellSubgraphSpec.Input.Type.Value(input_type))
        return tensor

    def add_cell_output(self, tensor, name):
        """Adds an output to the current CellSubgraphSpec.

        Args:
          tensor: Tensor to add as a cell output.
          name: Logical name of the cell output.

        Raises:
          RuntimeError: If the cell has already been exported.
        """
        if not self._cell_subgraph_spec:
            raise RuntimeError('already exported a CellSubgraphSpec')

        self._cell_subgraph_spec.output.add(name=name, tensor=tensor.name)


def update_tensor_arrays(network_tensors, arrays):
    """Updates a list of tensor arrays from the network's output tensors.

    Arguments:
      network_tensors: Output tensors from the underlying NN unit.
      arrays: TensorArrays to be updated.

    Returns:
      New list of TensorArrays after writing activations.
    """
    # TODO(googleuser): Only store activations that will be used later in linked
    # feature specifications.
    next_arrays = []
    for index, network_tensor in enumerate(network_tensors):
        array = arrays[index]
        size = array.size()
        array = array.write(size, network_tensor)
        next_arrays.append(array)
    return next_arrays


class DynamicComponentBuilder(ComponentBuilderBase):
    """Component builder for recurrent DRAGNN networks.

    Feature extraction and annotation are done sequentially in a tf.while_loop
    so fixed and linked features can be recurrent.
    """

    def __init__(self, master, component_spec):
        """Initializes the DynamicComponentBuilder from specifications.

        Args:
          master: dragnn.MasterBuilder object.
          component_spec: dragnn.ComponentSpec proto to be built.
        """
        super(DynamicComponentBuilder, self).__init__(
            master,
            component_spec,
            attr_defaults={'loss_function': 'softmax_cross_entropy'})

    def build_greedy_training(self, state, network_states):
        """Builds a training loop for this component.

        This loop repeatedly evaluates the network and computes the loss, but it
        does not advance using the predictions of the network. Instead, it advances
        using the oracle defined in the underlying transition system. The final
        state will always correspond to the gold annotation.

        Args:
          state: MasterState from the 'AdvanceMaster' op that advances the
            underlying master to this component.
          network_states: NetworkState object containing component TensorArrays.

        Returns:
          (state, cost, correct, total) -- These are TF ops corresponding to
          the final state after unrolling, the total cost, the total number of
          correctly predicted actions, and the total number of actions.
        """
        logging.info('Building component: %s', self.spec.name)
        # Add 0 to training_beam_size to disable eager static evaluation.
        # This is possible because tensorflow's constant_value does not
        # propagate arithmetic operations.
        with tf.control_dependencies(
            [tf.assert_equal(self.training_beam_size + 0, 1)]):
            stride = state.current_batch_size * self.training_beam_size
        self.network.pre_create(stride)

        cost = tf.constant(0.)
        correct = tf.constant(0)
        total = tf.constant(0)

        def cond(handle, *_):
            all_final = dragnn_ops.emit_all_final(handle, component=self.name)
            return tf.logical_not(tf.reduce_all(all_final))

        def body(handle, cost, correct, total, *arrays):
            """Runs the network and advances the state by a step."""

            with tf.control_dependencies([handle, cost, correct, total] +
                                         [x.flow for x in arrays]):
                # Get a copy of the network inside this while loop.
                updated_state = MasterState(handle, state.current_batch_size)
                network_tensors = self._feedforward_unit(
                    updated_state, arrays, network_states, stride, during_training=True)

                # Every layer is written to a TensorArray, so that it can be backprop'd.
                next_arrays = update_tensor_arrays(network_tensors, arrays)
                loss_function = self.attr('loss_function')
                with tf.control_dependencies([x.flow for x in next_arrays]):
                    with tf.name_scope('compute_loss'):
                        logits = self.network.get_logits(network_tensors)
                        if loss_function == 'softmax_cross_entropy':
                            gold = dragnn_ops.emit_oracle_labels(handle, component=self.name)
                            new_cost, new_correct, new_total, valid_logits, valid_gold = (
                                build_softmax_cross_entropy_loss(logits, gold))

                            if (self.eligible_for_self_norm and
                                self.master.hyperparams.self_norm_alpha > 0):
                                log_z = tf.reduce_logsumexp(valid_logits, [1])
                                new_cost += (self.master.hyperparams.self_norm_alpha *
                                             tf.nn.l2_loss(log_z))
                        elif loss_function == 'sigmoid_cross_entropy':
                            indices, gold, probs = (
                                dragnn_ops.emit_oracle_labels_and_probabilities(
                                    handle, component=self.name))
                            new_cost, new_correct, new_total, valid_gold = (
                                build_sigmoid_cross_entropy_loss(logits, gold, indices,
                                                                 probs))
                        else:
                            RuntimeError("Unknown loss function '%s'" % loss_function)

                        cost += new_cost
                        correct += new_correct
                        total += new_total

                with tf.control_dependencies([cost, correct, total, valid_gold]):
                    handle = dragnn_ops.advance_from_oracle(handle, component=self.name)
                return [handle, cost, correct, total] + next_arrays

        with tf.name_scope(self.name + '/train_state'):
            init_arrays = []
            for layer in self.network.layers:
                init_arrays.append(layer.create_array(state.current_batch_size))

        output = tf.while_loop(
            cond,
            body, [state.handle, cost, correct, total] + init_arrays,
            name='train_%s' % self.name)

        # Saves completed arrays and return final state and cost.
        state.handle = output[0]
        cost = output[1]
        correct = output[2]
        total = output[3]
        arrays = output[4:]

        # Store handles to the final output for use in subsequent tasks.
        network_state = network_states[self.name]
        with tf.name_scope(self.name + '/stored_act'):
            for index, layer in enumerate(self.network.layers):
                network_state.activations[layer.name] = network_units.StoredActivations(
                    array=arrays[index])

        # Normalize the objective by the total # of steps taken.
        # Note: Total could be zero by a number of reasons, including:
        #   * Oracle labels not being emitted.
        #   * All oracle labels for a batch are unknown (-1).
        #   * No steps being taken if component is terminal at the start of a batch.
        with tf.control_dependencies([tf.assert_greater(total, 0)]):
            cost /= tf.to_float(total)

        # Adds regularization for the hidden weights.
        cost = self.add_regularizer(cost)

        with tf.control_dependencies([x.flow for x in arrays]):
            return tf.identity(state.handle), cost, correct, total

    def build_greedy_inference(self, state, network_states,
                               during_training=False):
        """Builds an inference loop for this component.

        Repeatedly evaluates the network and advances the underlying state according
        to the predicted scores.

        Args:
          state: MasterState from the 'AdvanceMaster' op that advances the
            underlying master to this component.
          network_states: NetworkState object containing component TensorArrays.
          during_training: whether the graph is being constructed during training

        Returns:
          Handle to the state once inference is complete for this Component.
        """
        logging.info('Building component: %s', self.spec.name)
        if during_training:
            stride = state.current_batch_size * self.training_beam_size
        else:
            stride = state.current_batch_size * self.inference_beam_size
        self.network.pre_create(stride)

        def cond(handle, *_):
            all_final = dragnn_ops.emit_all_final(handle, component=self.name)
            return tf.logical_not(tf.reduce_all(all_final))

        def body(handle, *arrays):
            """Runs the network and advances the state by a step."""

            with tf.control_dependencies([handle] + [x.flow for x in arrays]):
                # Get a copy of the network inside this while loop.
                updated_state = MasterState(handle, state.current_batch_size)
                network_tensors = self._feedforward_unit(
                    updated_state,
                    arrays,
                    network_states,
                    stride,
                    during_training=during_training)
                next_arrays = update_tensor_arrays(network_tensors, arrays)
                with tf.control_dependencies([x.flow for x in next_arrays]):
                    if self.num_actions == 1:  # deterministic; take oracle transition
                        handle = dragnn_ops.advance_from_oracle(handle, component=self.name)
                    else:  # predict next transition using network logits
                        logits = self.network.get_logits(network_tensors)
                        logits = tf.cond(self.locally_normalize,
                                         lambda: tf.nn.log_softmax(logits), lambda: logits)
                        handle = dragnn_ops.advance_from_prediction(
                            handle, logits, component=self.name)
                return [handle] + next_arrays

        # Create the TensorArray's to store activations for downstream/recurrent
        # connections.
        with tf.name_scope(self.name + '/inference_state'):
            init_arrays = []
            for layer in self.network.layers:
                init_arrays.append(layer.create_array(stride))
        output = tf.while_loop(
            cond,
            body, [state.handle] + init_arrays,
            name='inference_%s' % self.name)

        # Saves completed arrays and returns final state.
        state.handle = output[0]
        arrays = output[1:]
        network_state = network_states[self.name]
        with tf.name_scope(self.name + '/stored_act'):
            for index, layer in enumerate(self.network.layers):
                network_state.activations[layer.name] = network_units.StoredActivations(
                    array=arrays[index])
        self._add_runtime_hooks()
        with tf.control_dependencies([x.flow for x in arrays]):
            return tf.identity(state.handle)

    def _feedforward_unit(self, state, arrays, network_states, stride,
                          during_training):
        """Constructs a single instance of a feed-forward cell.

        Given an input state and access to the arrays storing activations, this
        function encapsulates creation of a single network unit. This will *not*
        create new variables.

        Args:
          state: MasterState for the state that will be used to extract features.
          arrays: List of TensorArrays corresponding to network outputs from this
            component. These are used for recurrent link features; the arrays from
            other components are used for stack-prop style connections.
          network_states: NetworkState object containing the TensorArrays from
            *all* components.
          stride: int Tensor with the current beam * batch size.
          during_training: Whether to build a unit for training (vs inference).

        Returns:
          List of tensors generated by the underlying network implementation.
        """
        with tf.variable_scope(self.name, reuse=True):
            fixed_embeddings = []
            for channel_id, feature_spec in enumerate(self.spec.fixed_feature):
                fixed_embedding = network_units.fixed_feature_lookup(
                    self, state, channel_id, stride, during_training)
                if feature_spec.is_constant:
                    fixed_embedding.tensor = tf.stop_gradient(fixed_embedding.tensor)
                fixed_embeddings.append(fixed_embedding)

            linked_embeddings = []
            for channel_id, feature_spec in enumerate(self.spec.linked_feature):
                if feature_spec.source_component == self.name:
                    # Recurrent feature: pull from the local arrays.
                    index = self.network.get_layer_index(feature_spec.source_layer)
                    source_array = arrays[index]
                    source_layer_size = self.network.layers[index].dim
                    linked_embeddings.append(
                        network_units.activation_lookup_recurrent(
                            self, state, channel_id, source_array, source_layer_size,
                            stride))
                else:
                    # Stackprop style feature: pull from another component's arrays.
                    source = self.master.lookup_component[feature_spec.source_component]
                    source_tensor = network_states[source.name].activations[
                        feature_spec.source_layer]
                    source_layer_size = source.network.get_layer_size(
                        feature_spec.source_layer)
                    linked_embeddings.append(
                        network_units.activation_lookup_other(
                            self, state, channel_id, source_tensor.dynamic_tensor,
                            source_layer_size))

            context_tensor_arrays = []
            for context_layer in self.network.context_layers:
                index = self.network.get_layer_index(context_layer.name)
                context_tensor_arrays.append(arrays[index])

            if self.spec.attention_component:
                logging.info('%s component has attention over %s', self.name,
                             self.spec.attention_component)
                source = self.master.lookup_component[self.spec.attention_component]
                network_state = network_states[self.spec.attention_component]
                with tf.control_dependencies(
                    [tf.assert_equal(state.current_batch_size, 1)]):
                    attention_tensor = tf.identity(
                        network_state.activations['layer_0'].bulk_tensor)

            else:
                attention_tensor = None

            tensors = self.network.create(fixed_embeddings, linked_embeddings,
                                          context_tensor_arrays, attention_tensor,
                                          during_training)

            if self.master.build_runtime_graph:
                for index, layer in enumerate(self.network.layers):
                    self.add_cell_output(tensors[index], layer.name)

            return tensors
