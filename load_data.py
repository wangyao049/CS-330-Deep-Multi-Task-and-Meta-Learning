import numpy as np
import os
import random
import tensorflow as tf
#from scipy import misc
import imageio

def get_images(paths, labels, nb_samples=None, shuffle=True):
    """
    Takes a set of character folders and labels and returns paths to image files
    paired with labels.
    Args:
        paths: A list of character folders
        labels: List or numpy array of same length as paths
        nb_samples: Number of images to retrieve per character
    Returns:
        List of (label, image_path) tuples
    """
    if nb_samples is not None:
        sampler = lambda x: random.sample(x, nb_samples)
    else:
        sampler = lambda x: x
    images_labels = [(i, os.path.join(path, image))
                     for i, path in zip(labels, paths)
                     for image in sampler(os.listdir(path))]
    if shuffle:
        random.shuffle(images_labels)
    return images_labels


def image_file_to_array(filename, dim_input):
    """
    Takes an image path and returns numpy array
    Args:
        filename: Image filename
        dim_input: Flattened shape of image
    Returns:
        1 channel image
    """
    #image = misc.imread(filename)
    image = imageio.imread(filename)
    image = image.reshape([dim_input])
    image = image.astype(np.float32) / 255.0
    image = 1.0 - image
    return image


class DataGenerator(object):
    """
    Data Generator capable of generating batches of Omniglot data.
    A "class" is considered a class of omniglot digits.
    """

    def __init__(self, num_classes, num_samples_per_class, config={}):
        """
        Args:
            num_classes: Number of classes for classification (K-way)
            num_samples_per_class: num samples to generate per class in one batch
            batch_size: size of meta batch size (e.g. number of functions)
        """
        self.num_classes = num_classes
        self.num_samples_per_class = num_samples_per_class
        

        config = {'sad':''}

        data_folder = config.get('data_folder', './omniglot_resized')
        self.img_size = config.get('img_size', (28, 28))

        self.dim_input = np.prod(self.img_size)
        self.dim_output = self.num_classes

        character_folders = [os.path.join(data_folder, family, character)
                             for family in os.listdir(data_folder)
                             if os.path.isdir(os.path.join(data_folder, family))
                             for character in os.listdir(os.path.join(data_folder, family))
                             if os.path.isdir(os.path.join(data_folder, family, character))]

        random.seed(42)
        random.shuffle(character_folders)
        num_val = 100
        num_train = 1100
        self.metatrain_character_folders = character_folders[: num_train]
        self.metaval_character_folders = character_folders[
            num_train:num_train + num_val]
        self.metatest_character_folders = character_folders[
            num_train + num_val:]
        print("Data generator initialized. Shape: [B, {}, {}, 784]".format(self.num_samples_per_class, self.num_classes))

    def sample_batch(self, batch_type, batch_size=1):#, k_samples=1, n_classes=5):
        """
        Samples a batch for training, validation, or testing
        Args:
            batch_type: train/val/test
        Returns:
            A a tuple of (1) Image batch and (2) Label batch where
            image batch has shape [B, K, N, 784] and label batch has shape [B, K, N, N]
            where B is batch size, K is number of samples per class, N is number of classes
        """
        n_classes  = self.num_classes
        k_samples  = self.num_samples_per_class
        
        if batch_type == "train":
            folders = self.metatrain_character_folders
        elif batch_type == "val":
            folders = self.metaval_character_folders
        else:
            folders = self.metatest_character_folders

        #############################
        #### YOUR CODE GOES HERE ####
        pixels = 28*28
        all_image_batches = np.ndarray((batch_size, k_samples, n_classes, pixels))
        all_label_batches = np.ndarray((batch_size, k_samples, n_classes, n_classes))
        #print("all_image_batches shape: ", all_image_batches.shape)
        for b in range(batch_size):
            # Take N samples from all alphabet folders
            sample_paths  = random.sample(folders, n_classes)
            sample_labels = [os.path.basename(os.path.split(family)[0]) for family in sample_paths]
            images_labels = get_images(sample_paths, sample_labels, k_samples)
            
            # TODO: COrrect use of dimension
            count = 0
            for k in range(k_samples):
                for n in range(n_classes):
                    #print(images_labels[count][1])
                    all_image_batches[b, k, n, :] = image_file_to_array(filename=images_labels[count][1], dim_input=pixels)
                    #print(np.repeat([images_labels[count][0]], n_classes, axis=0))
                    #all_label_batches[b, k, n, :] = np.repeat([images_labels[count][0]], n_classes, axis=0)
                    # Labels as one-hot vectors
                    #all_label_batches[b, k, n, :] = tf.one_hot(indices=n, depth=n_classes)
                    all_label_batches[b, k, n, :] = np.zeros(n_classes)
                    all_label_batches[b, k, n, n] = 1
                    count += 1
            #############################
        #print("Batch of images of shape:", all_image_batches.shape)
        #print("Batch of labels of shape:", all_label_batches.shape)
        return all_image_batches, all_label_batches