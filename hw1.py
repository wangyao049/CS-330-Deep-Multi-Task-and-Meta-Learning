import numpy as np
import random
import tensorflow as tf
from load_data import DataGenerator
from tensorflow.python.platform import flags
from tensorflow.keras import layers

FLAGS = flags.FLAGS

flags.DEFINE_integer(
    'num_classes', 5, 'number of classes used in classification (e.g. 5-way classification).')

flags.DEFINE_integer('num_samples', 1,
                     'number of examples used for inner gradient update (K for K-shot learning).')

flags.DEFINE_integer('meta_batch_size', 16,
                     'Number of N-way classification tasks per batch')


def loss_function(preds, labels):
    """
    Computes MANN loss
    Args:
        preds: [B, K+1, N, N] network output
        labels: [B, K+1, N, N] labels
    Returns:
        scalar loss
    """
    #############################
    #### YOUR CODE GOES HERE ####
    #print(preds.shape)
    #print(labels[0,:,:,:].shape)
    #bce  = tf.keras.losses.BinaryCrossentropy()
    #loss = bce(preds, labels)
    #tf.expand_dims(t, 0) 
    #if labels.get_shape().as_list()[0] == None :
    #    print("None shape")
    #    loss = tf.losses.softmax_cross_entropy(labels[0,:,:,:], preds, reduction='weighted_sum')
    #else:
    #    print("not None shape")
    #    loss = tf.losses.softmax_cross_entropy(labels, preds, reduction='weighted_sum')
    #new_shape = labels.get_shape().as_list()[-3:]
    #labels = tf.reshape(labels, tf.TensorShape(new_shape))
    loss = tf.losses.softmax_cross_entropy(labels, preds, reduction='weighted_sum')
    return loss
    
    #############################


class MANN(tf.keras.Model):

    def __init__(self, num_classes, samples_per_class):
        super(MANN, self).__init__()
        self.num_classes = num_classes
        self.samples_per_class = samples_per_class
        self.layer1 = tf.keras.layers.LSTM(128, return_sequences=True)
        self.layer2 = tf.keras.layers.LSTM(num_classes, return_sequences=True)

    def call(self, input_images, input_labels):
        """
        MANN
        Args:
            input_images: [B, K+1, N, 784] flattened images
            labels:       [B, K+1, N, N] ground truth labels
        Returns:
            [B, K+1, N, N] predictions
        """
        #############################
        #### YOUR CODE GOES HERE ####
        batchs = input_images.shape[0]
        out = np.ndarray([16,
                          input_images.shape[1],
                          input_images.shape[2],
                          input_images.shape[3] ])
        for i in range(16):
            out[i,:,:,:] = self.layer1(input_images[i,:,:,:])#[i,:,:,:])
            out[i,:,:,:] = self.layer2(out)
        #out = np.ones((1,2,5,784))
        #############################
        return out

ims = tf.placeholder(tf.float32, shape=(
    None, FLAGS.num_samples + 1, FLAGS.num_classes, 784))
labels = tf.placeholder(tf.float32, shape=(
    None, FLAGS.num_samples + 1, FLAGS.num_classes, FLAGS.num_classes))

data_generator = DataGenerator(
    FLAGS.num_classes, FLAGS.num_samples + 1)

o = MANN(FLAGS.num_classes, FLAGS.num_samples + 1)
out = o(ims, labels)

loss = loss_function(out, labels)
#optim = tf.train.AdamOptimizer(0.001)
optim = tf.compat.v1.train.AdamOptimizer(0.001)
optimizer_step = optim.minimize(loss)
print("Starts training...")
with tf.compat.v1.Session() as sess:
    sess.run(tf.local_variables_initializer())
    sess.run(tf.global_variables_initializer())
    
    for step in range(50000):
        i, l = data_generator.sample_batch('train', batch_size=16)#FLAGS.meta_batch_size)
        #print("i.shape:",i.shape)
        feed = {ims:    i.astype(np.float32),
                labels: l.astype(np.float32)}
        #print("feed[ims].shape:", feed[ims].shape)
        _, ls = sess.run([optimizer_step, loss], feed)

        if step % 100 == 0:
            print("*" * 5 + "Iter " + str(step) + "*" * 5)
            i, l = data_generator.sample_batch('test', 100)
            feed = {ims:    i.astype(np.float32),
                    labels: l.astype(np.float32)}
            pred, tls = sess.run([out, loss], feed)
            print("Train Loss:", ls, "Test Loss:", tls)
            pred = pred.reshape(
                -1, FLAGS.num_samples + 1,
                FLAGS.num_classes, FLAGS.num_classes)
            pred = pred[:, -1, :, :].argmax(2)
            l = l[:, -1, :, :].argmax(2)
            print("Test Accuracy", (1.0 * (pred == l)).mean())
