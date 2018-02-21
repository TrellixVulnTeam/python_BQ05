#Copyright (C) 2016 Paolo Galeone <nessuno@nerdz.eu>
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, You can obtain one at http://mozilla.org/MPL/2.0/.
#Exhibit B is not attached; this software is compatible with the
#licenses expressed under Section 1.12 of the MPL v2.
"""utils contains utilities to work with tensorflow
and make the summary generation easier """

import tensorflow as tf


def print_graph_ops(graph):
    """used in debug: print graph operations"""
    ops = graph.get_operations()
    for operation in ops:
        print("Op name: %s" % operation.name)
        for k in operation.inputs:
            print("\tin: %s %s" % (k.name, k.get_shape()))
        for k in operation.outputs:
            print("\tout: %s %s" % (k.name, k.get_shape()))
        print("")


def log_histogram(var, name):
    """log_histogram creates and histogrm summary for var, with name
    The returned value can be discarded if the function has been called inside the default graph.

    Remeber to call tf.summary.merge_all() before tf.global_variables_initializer()
    """

    with tf.name_scope("summaries"):
        return tf.summary.histogram(name, var)


def weight(shape,
           name,
           initializer=tf.contrib.layers.xavier_initializer_conv2d()):
    """ weight returns a tensor with the requested shape, initialized with
    the xavier initializer, if not other initializer is specified.
    Creates baisc summaries too.
    Returns the weight tensor"""
    parameters = tf.get_variable(name, shape, initializer=initializer)
    _ = log_histogram(parameters, parameters.name)
    return parameters


def kernels(shape,
            name,
            initializer=tf.contrib.layers.xavier_initializer_conv2d()):
    """ kernels create and return a weight with the required shape
    The main difference with weight, is that kernels returns the summary
    for the learned filters visualization if the weight depth is 1, 2 or 3.
    shape should be in the form [ Y, X, Depth, NumKernels ].

    Initializes the kernels with the xavier initializer if no other initializer
    is specified.
    """
    parameters = weight(shape, name, initializer)

    if shape[2] in (1, 3, 4):
        with tf.name_scope("summaries"):
            num_kernels = shape[3]
            depth = shape[2]
            max_outputs = int(num_kernels / depth)
            tf.summary.image(
                name,
                tf.reshape(parameters,
                           [num_kernels, shape[0], shape[1], depth]),
                max_outputs=max_outputs)
    return parameters


def bias(shape, name, init_val=0.0):
    """ bias returns a tensor with the requested shape, initialized with init_val.
    Creates summaries too.
    Returns the bias"""
    biases = tf.get_variable(
        name, shape, initializer=tf.constant_initializer(init_val))
    _ = log_histogram(biases, biases.name)
    return biases


def padder(input_v, output_v):
    """Extract the borders from input_v.
    The borders size is the difference between output and input height and width.

    If the input depth and the output depth is the same, the padding is made layer by layer.
    eg: padding of layer with depth 1, will be attached to the output layer with depth 1 ecc

    Othwerwise, if the output depth is greather than the input depth (thats the case in
    convolutional neural networks, when output is series of images resulting from
    the convolution of a set of kernels),
    it pads every output layer with the average of the extract border of input.

    input_v: a tensor with [input_batch_size, height, width, input_depth]
    output_v: a tensor with [output_batch_size, reduced_height, reduced_width, output_depth]

    @returns:
        the output volume, padded with the borders of input. Accordingly to the previous description
    """
    input_depth = input_v.get_shape()[3].value
    width = input_v.get_shape()[2].value
    height = input_v.get_shape()[1].value

    output_depth = output_v.get_shape()[3].value
    reduced_width = output_v.get_shape()[2].value
    reduced_height = output_v.get_shape()[1].value

    assert (width - reduced_width) % 2 == 0
    assert (height - reduced_height) % 2 == 0
    assert output_depth >= input_depth

    width_diff = int((width - reduced_width) / 2)
    height_diff = int((height - reduced_height) / 2)

    # every image in the batch have the depth reduced from X to 1 (collpased depth)
    # this single depth is the sum of every depth of the image
    # Or of every depth of the general input volume.
    input_collapsed = tf.reduce_mean(
        input_v, reduction_indices=[3], keep_dims=True)

    # lets make the input depth equal to the output depth
    input_expanded = input_collapsed
    for _ in range(output_depth - 1):
        input_expanded = tf.concat(3, [input_expanded, input_collapsed])

    padding_top = tf.slice(input_expanded, [0, 0, width_diff, 0],
                           [-1, height_diff, reduced_width, -1])
    padding_bottom = tf.slice(input_expanded,
                              [0, height - height_diff, width_diff, 0],
                              [-1, height_diff, reduced_width, -1])
    padded = tf.concat(1, [padding_top, output_v, padding_bottom])

    padding_left = tf.slice(input_expanded, [0, 0, 0, 0],
                            [-1, height, width_diff, -1])
    padding_right = tf.slice(input_expanded, [0, 0, width - width_diff, 0],
                             [-1, height, height_diff, -1])

    padded = tf.concat(2, [padding_left, padded, padding_right])
    return padded
