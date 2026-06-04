import math
import numpy as np
from NumpyModel.ActivationFunctions import activation_functions


class Layer(object):
    def __init__(self, **kwargs):
        allowed_kwargs = {'input_shape',
                          'name',
                          'trainable',
                          'weights'
                          }
        for kwarg in kwargs:
            if kwarg not in allowed_kwargs:
                raise TypeError('Keyword argument not understood:', kwarg)
        name = kwargs.get('name')
        if not name:
            name = self.__class__.__name__
        self.name = name

        self.trainable = kwargs.get('trainable', True)
        if 'input_shape' in kwargs:
            self.input_shape = kwargs['input_shape']

        if 'weights' in kwargs:
            self.initial_weights = kwargs['weights']
        else:
            self.initial_weights = None

    def parameters(self):
        """ The number of trainable parameters used by the layer """
        return 0

    def forward_pass(self, X, training):
        """ Propogates the signal forward in the network """
        raise NotImplementedError()

    def output_shape(self):
        """ The shape of the output produced by forward_pass """
        raise NotImplementedError()


class Dense(Layer):
    """A fully-connected NN layer.
    Parameters:
    -----------
    n_units: int
        The number of neurons in the layer.
    input_shape: tuple
        The expected input shape of the layer. For dense layers a single digit specifying
        the number of features of the input. Must be specified if it is the first layer in
        the network.
    """
    def __init__(self, n_units, input_shape=None, activation=None):
        self.layer_input = None
        self.input_shape = input_shape
        self.n_units = n_units
        self.trainable = True
        self.activation = activation
        self.W = None
        self.w0 = None

    def initialize(self, optimizer):
        # Initialize the weights
        limit = 1 / math.sqrt(self.input_shape[0])
        self.W  = np.random.uniform(-limit, limit, (self.input_shape[0], self.n_units))
        self.w0 = np.zeros((1, self.n_units))

    def parameters(self):
        return np.prod(self.W.shape) + np.prod(self.w0.shape)

    def forward_pass(self, X, training=True):
        self.layer_input = X
        res = X.dot(self.W) + self.w0
        if not self.activation:
            return res
        else:
            activator = activation_functions[self.activation]()
            return activator(res)

    def output_shape(self):
        return self.n_units,


class TFLSTM(Layer):

    def __init__(self, n_units, input_shape=None, activation='tanh',
                 recurrent_activation='sigmoid', return_sequence=True):

        self.input_shape = input_shape
        self.time_steps = input_shape[0]
        self.input_dim = input_shape[1]
        self.n_units = n_units
        self.activation = activation_functions[activation]()
        self.recurrent_activation = activation_functions[recurrent_activation]()
        self.return_sequence = return_sequence
        self.trainable = True

        limit = 1 / math.sqrt(self.input_dim)
        self._kernel = np.random.uniform(-limit, limit, (self.input_dim + self.n_units, 4 * self.n_units))
        self._bias = np.zeros(4 * self.n_units)

    def initialize(self, optimizer):
        limit = 1 / math.sqrt(self.input_dim)
        self._kernel = np.random.uniform(-limit, limit, (self.input_dim + self.n_units, 4 * self.n_units))
        self._bias = np.zeros(4 * self.n_units)

    def parameters(self):
        return (self.n_units * (self.n_units + self.input_dim) + self.n_units) * 4

    def forward_pass(self, X, training=True):
        batch_size, time_steps, input_dim = X.shape

        # Save these values for use in backprop.
        self.h_states = np.zeros((batch_size, time_steps + 1, self.n_units))
        self.c_states = np.zeros((batch_size, time_steps + 1, self.n_units))
        self.outputs = np.zeros((batch_size, time_steps, self.n_units))

        # Set last time step to zero for calculation of the state_input at time step zero
        for t in range(time_steps):
            # Input to state_t is the current input and output of previous states
            x = X[:, t, :]
            h_last = self.h_states[:, t, :]
            c_last = self.c_states[:, t, :]
            lstm_matrix = np.dot(np.concatenate([x, h_last], axis=1), self._kernel) + self._bias
            zi, zj, zf, zo = np.split(lstm_matrix, 4, axis=1)
            ct = self.recurrent_activation(zf + 1.0) * c_last + self.recurrent_activation(zi) * self.activation(zj)
            ht = self.recurrent_activation(zo) * self.activation(ct)
            self.c_states[:, t + 1, :] = ct
            self.h_states[:, t + 1, :] = ht

        self.outputs = self.h_states[:, 1:, :]

        if self.return_sequence:
            return self.outputs
        else:
            return self.outputs[:, -1, :]

    def output_shape(self):
        if self.return_sequence:
            return self.time_steps, self.n_units
        else:
            return self.n_units,

class Conv2D(Layer):
    """A 2D Convolution Layer.

    Parameters:
    -----------
    n_filters: int
        The number of filters that will convolve over the input matrix. The number of channels
        of the output shape.
    filter_shape: tuple
        A tuple (filter_height, filter_width).
    input_shape: tuple
        The shape of the expected input of the layer. (batch_size, channels, height, width)
        Only needs to be specified for first layer in the network.
    padding: string
        Either 'same' or 'valid'. 'same' results in padding being added so that the output height and width
        matches the input height and width. For 'valid' no padding is added.
    stride: int
        The stride length of the filters during the convolution over the input.
    """
    def __init__(self, n_filters, filter_shape, input_shape=None, padding='same', stride=1, activation=None):
        self.n_filters = n_filters
        self.filter_shape = filter_shape
        self.padding = padding
        self.stride = stride
        self.input_shape = input_shape
        self.trainable = True
        self.activation = activation

    def initialize(self, optimizer):
        # Initialize the weights
        filter_height, filter_width = self.filter_shape
        channels = self.input_shape[0]
        limit = 1 / math.sqrt(np.prod(self.filter_shape))
        self.W  = np.random.uniform(-limit, limit, size=(self.n_filters, channels, filter_height, filter_width))
        self.w0 = np.zeros((self.n_filters, 1))

    def parameters(self):
        return np.prod(self.W.shape) + np.prod(self.w0.shape)

    def forward_pass(self, X, training=True):
        batch_size, channels, height, width = X.shape
        # Turn image shape into column shape
        # (enables dot product between input and weights)
        X_col = image_to_column(X, self.filter_shape, stride=self.stride, output_shape=self.padding)
        # Turn weights into column shape
        W_col = self.W.reshape((self.n_filters, -1))
        # Calculate output
        output = W_col.dot(X_col) + self.w0
        # Reshape into (n_filters, out_height, out_width, batch_size)
        output = output.reshape(self.output_shape() + (batch_size, ))
        # Redistribute axises so that batch size comes first
        if not self.activation:
            return output.transpose(3, 0, 1, 2)
        else:
            activator = activation_functions[self.activation]()
            return activator(output.transpose(3, 0, 1, 2))

    def output_shape(self):
        channels, height, width = self.input_shape
        pad_h, pad_w = determine_padding(self.filter_shape, output_shape=self.padding)
        output_height = (height + np.sum(pad_h) - self.filter_shape[0]) / self.stride + 1
        output_width = (width + np.sum(pad_w) - self.filter_shape[1]) / self.stride + 1
        return self.n_filters, int(output_height), int(output_width)


class PoolingLayer(Layer):
    """A parent class of MaxPooling2D and AveragePooling2D
    """
    def __init__(self, pool_shape=(2, 2), stride=1, input_shape=None, padding='valid'):
        self.pool_shape = pool_shape
        self.stride = stride
        self.padding = padding
        self.input_shape = input_shape
        self.trainable = True

    def forward_pass(self, X, training=True):
        batch_size, channels, height, width = X.shape

        _, out_height, out_width = self.output_shape()

        X = X.reshape(batch_size * channels, 1, height, width)
        X_col = image_to_column(X, self.pool_shape, self.stride, self.padding)

        # MaxPool or AveragePool specific method
        output = self._pool_forward(X_col)

        output = output.reshape(out_height, out_width, batch_size, channels)
        output = output.transpose(2, 3, 0, 1)

        return output


    def output_shape(self):
        channels, height, width = self.input_shape
        if isinstance(self.stride, int):
            h_stride, w_stride = self.stride, self.stride
        else:
            h_stride, w_stride = self.stride

        self.pad_h, self.pad_w = determine_padding(self.pool_shape, self.padding)

        out_height = (height - self.pool_shape[0] + self.pad_h[0] + self.pad_h[1]) // h_stride + 1
        out_width = (width - self.pool_shape[1] + self.pad_w[0] + self.pad_w[1]) // w_stride + 1
        if self.padding == 'same':
            out_height = int(math.ceil(out_height))
            out_width = int(math.ceil(out_width))
        else:
            out_height = int(math.floor(out_height))
            out_width = int(math.floor(out_width))
        assert out_height % 1 == 0
        assert out_width % 1 == 0
        return channels, int(out_height), int(out_width)


class MaxPooling2D(PoolingLayer):
    def _pool_forward(self, X_col):
        arg_max = np.argmax(X_col, axis=0).flatten()
        output = X_col[arg_max, range(arg_max.size)]
        self.cache = arg_max
        return output


class AveragePooling2D(PoolingLayer):
    def _pool_forward(self, X_col):
        output = np.mean(X_col, axis=0)
        return output


class Flatten(Layer):
    """ Turns a multidimensional matrix into two-dimensional """
    def __init__(self, input_shape=None):
        self.prev_shape = None
        self.trainable = True
        self.input_shape = input_shape

    def forward_pass(self, X, training=True):
        self.prev_shape = X.shape
        return X.reshape((X.shape[0], -1))

    def output_shape(self):
        return np.prod(self.input_shape),


class Reshape(Layer):
    """ Reshapes the input tensor into specified shape

    Parameters:
    -----------
    shape: tuple
        The shape which the input shall be reshaped to.
    """
    def __init__(self, output_shape, input_shape=None):
        self.prev_shape = None
        self.trainable = True
        self.shape = output_shape
        self.input_shape = input_shape

    def forward_pass(self, X, training=True):
        self.prev_shape = X.shape
        return X.reshape((X.shape[0], ) + self.shape)

    def output_shape(self):
        return self.shape

class Permute(Layer):
    """ Reshapes the input tensor into specified shape

    Parameters:
    -----------
    shape: tuple
        The shape which the input shall be reshaped to.
    """
    def __init__(self, output_shape, perm=(2,1), input_shape=None):
        self.perm = perm
        self.prev_shape = None
        self.trainable = True
        self.shape = output_shape
        self.input_shape = input_shape

    def forward_pass(self, X, training=True):
        self.prev_shape = X.shape
        return X.transpose((0, *self.perm))

    def output_shape(self):
        return self.shape


# Method which calculates the padding based on the specified output shape and the
# shape of the filters
def determine_padding(filter_shape, output_shape="same"):

    # No padding
    if output_shape == "valid":
        return (0, 0), (0, 0)
    # Pad so that the output shape is the same as input shape (given that stride=1)
    elif output_shape == "same":
        filter_height, filter_width = filter_shape

        # Derived from:
        # output_height = (height + pad_h - filter_height) / stride + 1
        # In this case output_height = height and stride = 1. This gives the
        # expression for the padding below.
        pad_h1 = int(math.floor((filter_height - 1) / 2))
        pad_h2 = int(math.ceil((filter_height - 1) / 2))
        pad_w1 = int(math.floor((filter_width - 1) / 2))
        pad_w2 = int(math.ceil((filter_width - 1) / 2))

        return (pad_h1, pad_h2), (pad_w1, pad_w2)


# Reference: CS231n Stanford
def get_im2col_indices(images_shape, filter_shape, padding, stride=1):
    # First figure out what the size of the output should be
    if isinstance(stride, int):
        h_stride, w_stride = stride, stride
    else:
        h_stride, w_stride = stride

    batch_size, channels, height, width = images_shape
    filter_height, filter_width = filter_shape
    pad_h, pad_w = padding
    out_height = int((height + np.sum(pad_h) - filter_height) / h_stride + 1)
    out_width = int((width + np.sum(pad_w) - filter_width) / w_stride + 1)

    i0 = np.repeat(np.arange(filter_height), filter_width)
    i0 = np.tile(i0, channels)
    i1 = h_stride * np.repeat(np.arange(out_height), out_width)
    j0 = np.tile(np.arange(filter_width), filter_height * channels)
    j1 = w_stride * np.tile(np.arange(out_width), out_height)
    i = i0.reshape(-1, 1) + i1.reshape(1, -1)
    j = j0.reshape(-1, 1) + j1.reshape(1, -1)

    k = np.repeat(np.arange(channels), filter_height * filter_width).reshape(-1, 1)

    return k, i, j


# Method which turns the image shaped input to column shape.
# Used during the forward pass.
# Reference: CS231n Stanford
def image_to_column(images, filter_shape, stride, output_shape='same'):
    filter_height, filter_width = filter_shape
    pad_h, pad_w = determine_padding(filter_shape, output_shape)
    # Add padding to the image
    images_padded = np.pad(images, ((0, 0), (0, 0), pad_h, pad_w), mode='constant')

    # Calculate the indices where the dot products are to be applied between weights
    # and the image
    k, i, j = get_im2col_indices(images.shape, filter_shape, (pad_h, pad_w), stride)
    # k, i, j = get_im2col_indices(images_padded.shape, filter_shape, (pad_h, pad_w), stride)

    # Get content from image at those indices
    cols = images_padded[:, k, i, j]
    channels = images.shape[1]
    # Reshape content into column shape
    cols = cols.transpose(1, 2, 0).reshape(filter_height * filter_width * channels, -1)
    return cols


# Method which turns the column shaped input to image shape.
# Used during the backward pass.
# Reference: CS231n Stanford
def column_to_image(cols, images_shape, filter_shape, stride, output_shape='same'):
    batch_size, channels, height, width = images_shape
    pad_h, pad_w = determine_padding(filter_shape, output_shape)
    height_padded = height + np.sum(pad_h)
    width_padded = width + np.sum(pad_w)
    images_padded = np.zeros((batch_size, channels, height_padded, width_padded))

    # Calculate the indices where the dot products are applied between weights
    # and the image
    k, i, j = get_im2col_indices(images_shape, filter_shape, (pad_h, pad_w), stride)

    cols = cols.reshape(channels * np.prod(filter_shape), -1, batch_size)
    cols = cols.transpose(2, 0, 1)
    # Add column content to the images at the indices
    np.add.at(images_padded, (slice(None), k, i, j), cols)

    # Return image without padding
    return images_padded[:, :, pad_h[0]:height+pad_h[0], pad_w[0]:width+pad_w[0]]
