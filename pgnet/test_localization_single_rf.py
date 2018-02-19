#Copyright (C) 2016 Paolo Galeone <nessuno@nerdz.eu>
#
#This Source Code Form is subject to the terms of the Mozilla Public
#License, v. 2.0. If a copy of the MPL was not distributed with this
#file, you can obtain one at http://mozilla.org/MPL/2.0/.
#Exhibit B is not attached; this software is compatible with the
#licenses expressed under Section 1.12 of the MPL v2.
"""test_localization_single_rf.py --image-path <img path>"""

import argparse
import os
import sys
import time
from collections import defaultdict
import tensorflow as tf
import cv2
import numpy as np
import train
from pgnet import model
from inputs import pascal
from inputs import image_processing
import utils

# detection parameters
RECT_SIMILARITY = 0.9


def main(args):
    """ main """

    if not os.path.exists(args.image_path):
        print("{} does not exists".format(args.image_path))
        return 1

    # export model.pb from session dir. Skip if model.pb already exists
    model.export(train.NUM_CLASSES, train.SESSION_DIR, "model-best-0",
                 train.MODEL_PATH)

    graph = model.load(train.MODEL_PATH, args.device)
    with graph.as_default():
        # (?, n, n, NUM_CLASSES) tensor
        logits = graph.get_tensor_by_name(model.OUTPUT_TENSOR_NAME + ":0")
        images_ = graph.get_tensor_by_name(model.INPUT_TENSOR_NAME + ":0")
        # each cell in coords (batch_position, i, j) -> is a probability vector
        per_region_probabilities = tf.nn.softmax(
            tf.reshape(logits, [-1, train.NUM_CLASSES]))
        # [tested positions, train.NUM_CLASSES]

        # array[0]=values, [1]=indices
        # get every probabiliy, because we can use localization to do classification
        top_k = tf.nn.top_k(per_region_probabilities, k=train.NUM_CLASSES)
        # each with shape [tested_positions, k]

        original_image = tf.image.convert_image_dtype(
            image_processing.read_image(
                tf.constant(args.image_path), 3,
                args.image_path.split('.')[-1]),
            dtype=tf.uint8)
        original_image_dim = tf.shape(original_image)

        k = 2
        eval_image_side = tf.cond(
            tf.less_equal(
                tf.minimum(original_image_dim[0], original_image_dim[1]),
                tf.constant(model.INPUT_SIDE)),
            lambda: tf.constant(model.INPUT_SIDE),
            lambda: tf.constant(model.INPUT_SIDE + model.DOWNSAMPLING_FACTOR * model.LAST_CONV_INPUT_STRIDE * k)
        )

        eval_image = tf.expand_dims(
            image_processing.zm_mp(
                image_processing.resize_bl(original_image, eval_image_side)), 0)

        with tf.Session(config=tf.ConfigProto(
                allow_soft_placement=True)) as sess:

            input_image, input_image_side, image = sess.run(
                [eval_image, eval_image_side, original_image])

            start = time.time()
            probability_map, top_values, top_indices = sess.run(
                [logits, top_k[0], top_k[1]], feed_dict={images_: input_image})

            # let's think to the net as a big net, with the last layer (before the FC
            # layers for classification) with a receptive field of
            # LAST_KERNEL_SIDE x LAST_KERNEL_SIDE. Lets approximate the net with this last kernel:
            # If the image is scaled down to  LAST_KERNEL_SIDE x LAST_KERNEL_SIDE
            # the output is a single point.
            # if the image is scaled down to something bigger
            # (that make the output side of contolution integer) the result is a spacial map
            # of points. Every point has a depth of num classes.

            # for every image in the input batch
            probability_coords = 0
            for _ in range(len(input_image)):
                # scaling factor between original image and resized image
                full_image_scaling_factors = np.array([
                    image.shape[1] / input_image_side,
                    image.shape[0] / input_image_side
                ])

                glance = defaultdict(list)
                # select count(*), avg(prob) from map group by label, order by count, avg.
                group = defaultdict(lambda: defaultdict(float))
                for pmap_y in range(probability_map.shape[1]):
                    # calculate position in the downsampled image ds
                    ds_y = pmap_y * model.LAST_CONV_OUTPUT_STRIDE
                    for pmap_x in range(probability_map.shape[2]):
                        ds_x = pmap_x * model.LAST_CONV_OUTPUT_STRIDE

                        if top_indices[probability_coords][
                                0] != pascal.BACKGROUND_CLASS_ID:

                            # create coordinates of rect in the downsampled image
                            # convert to numpy array in order to use broadcast ops
                            coord = [
                                ds_x, ds_y, ds_x + model.LAST_KERNEL_SIDE,
                                ds_y + model.LAST_KERNEL_SIDE
                            ]
                            # if something is found, append rectagle to the
                            # map of rectalges per class
                            rect = utils.upsample_and_shift(
                                coord, model.DOWNSAMPLING_FACTOR, [0, 0],
                                full_image_scaling_factors)

                            prob = top_values[probability_coords][0]
                            label = pascal.CLASSES[top_indices[
                                probability_coords][0]]

                            rect_prob = [rect, prob]
                            glance[label].append(rect_prob)
                            group[label]["count"] += 1
                            group[label]["prob"] += prob

                        # update probability coord value
                        probability_coords += 1

                classes = group.keys()
                print('Found {} classes: {}'.format(len(classes), classes))

                # find out the minimum amount of intersection among regions
                # in the original image, that can be used to trigger a match
                # or 2, is s square. 0 dim is batch
                map_side = probability_map.shape[1]
                map_area = map_side**2

                min_intersection = map_side
                print('min intersection: ', min_intersection)

                # Save the relative frequency for every class
                # To trigger a match, at least a fraction of intersection should be present
                for label in group:
                    group[label]["prob"] /= group[label]["count"]
                    group[label]["rf"] = group[label]["count"] / map_area
                    print(label, group[label])

                # merge overlapping rectangles for each class.
                # return a map of {"label": [rect, prob, count]
                localize = utils.group_overlapping_regions(
                    glance, eps=RECT_SIMILARITY)
                end_time = time.time() - start
                print("time: {}".format(end_time))

                # now I can convert RGB to BGR to display image with OpenCV
                # I can't do that before, because ROIs gets extracted on RGB image
                # in order to be processed without errors by Tensorflow
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                for label, rect_prob_list in localize.items():
                    for rect_prob in rect_prob_list:
                        rect = rect_prob[0]
                        prob = rect_prob[1]
                        count = rect_prob[2]
                        freq = group[label]["rf"]
                        if count >= min_intersection and freq > 0.1:
                            utils.draw_box(
                                image,
                                rect,
                                "{}({:.3})".format(label, prob),
                                utils.LABEL_COLORS[label],
                                thickness=2)

                cv2.imshow("img", image)
                cv2.waitKey(0)
                return 0


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        description="Apply the model to image-path")
    PARSER.add_argument("--device", default="/gpu:1")
    PARSER.add_argument("--image-path")
    sys.exit(main(PARSER.parse_args()))
