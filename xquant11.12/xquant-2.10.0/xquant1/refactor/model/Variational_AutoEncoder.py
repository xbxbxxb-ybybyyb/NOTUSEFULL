'''This script demonstrates how to build a variational autoencoder with Keras.
Reference: "Auto-Encoding Variational Bayes" https://arxiv.org/abs/1312.6114
'''
import numpy as np
from scipy.stats import norm

from keras.layers import Input, Dense, Lambda
from keras.models import Model
from keras import backend as K
from keras import objectives


"""

"""
def get_VAE(input_dim, encoder_layers, decoder_layers, optimizer,loss):
    #encoder
    input_layer = Input(shape=(input_dim,))
    for lidx, layer in enumerate(encoder_layers):
        if lidx == 0:
            x = Dense(layer, activation='relu')(input_layer)
        elif lidx == len(encoder_layers)-1:
             z_mean = Dense(layer)(x)
             z_log_var = Dense(layer)(x)
        else:
            x = Dense(layer, activation='relu')(x)
   
    #sampling
    def sampling(args):
        z_mean, z_log_var = args
        epsilon = K.random_normal(shape=(encoder_layers[-1],), mean=0.)
                                 
        return z_mean + K.exp(z_log_var / 2) * epsilon
    
    z = Lambda(sampling, output_shape=(encoder_layers[-1],))([z_mean, z_log_var])
    
    # decoder
    x = Dense(encoder_layers[-1], activation='relu')(z)
    for layer in decoder_layers:
        x = Dense(layer, activation='relu')(x)

    x_decoded_mean = Dense(input_dim, activation='sigmoid')(x)
    
    #loss
    def vae_loss(x, x_decoded_mean):
        xent_loss = input_dim * objectives.binary_crossentropy(x, x_decoded_mean)
        kl_loss = - 0.5 * K.sum(1 + z_log_var - K.square(z_mean) - K.exp(z_log_var), axis=-1)
        return xent_loss + kl_loss
    
    vae = Model(input_layer, x_decoded_mean)
    encoder = Model(input_layer, z_mean)
    vae.compile(optimizer = optimizer, loss=vae_loss)
    
    return vae, encoder


def VAE_train(X_train, X_vali, encoder_layers, decoder_layers, optimizer = 'RMSprop', loss = "mse", batch_size=30, epoches = 2000):
    from keras.callbacks import ReduceLROnPlateau,EarlyStopping
        
    vae_model,encoder = get_VAE(X_train.shape[1], encoder_layers, decoder_layers, optimizer, loss)
    reduce_lr = ReduceLROnPlateau(patience = 15)
    early_stopping = EarlyStopping(patience = 50)
    
    history = vae_model.fit(X_train, X_train,
            shuffle=True,
            nb_epoch=epoches,
            batch_size=batch_size,
            validation_data=(X_vali, X_vali), 
            callbacks=[reduce_lr, early_stopping])

    print(history)
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    return vae_model, encoder