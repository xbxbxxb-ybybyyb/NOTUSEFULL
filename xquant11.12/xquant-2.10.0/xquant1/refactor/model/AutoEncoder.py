# -*- coding: utf-8 -*-
"""
Created on Wed Aug 15 10:23:00 2018
@author: 013150
"""

#%%(5)搭建自编码器模型
"""
layers: list,全连接层，每层的维度。
"""
def get_autoEncoder(input_dim, encoder_layers, decoder_layers, optimizer,loss):
    from keras.layers import Input,Dense
    from keras.models import Model

    input_layer = Input((input_dim,))
    
    for lidx, layer in enumerate(encoder_layers):
        if lidx == 0:
            x = Dense(layer, input_dim = input_dim, activation='relu')(input_layer)
        else:
            x = Dense(layer, input_dim = input_dim, activation='relu')(x)
    encoder = x
    
    for layer in decoder_layers:
        x = Dense(layer, activation='relu')(x)
    x = Dense(input_dim, activation='relu')(x)
    
    AE_model = Model(input_layer, x)
    encode_model = Model(input_layer, encoder)
    AE_model.compile(optimizer = optimizer, loss=loss,metrics=["mse"])
    
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    
    return AE_model,encode_model

"""
参数：
    X_train：训练集，array，一行一个样本    
    X_vali：验证集，array，一行一个样本
    encoder_layers：array,编码层每层的神经元数
    decoder_layers：array，解码层每层的神经元数
    optimizer: 'SGD', 'RMSprop', 'Adagrad', 'Adadelta', 'Adam', 'Adamax', 'Nadam'
    loss: "mse", "categorical_crossentropy"
"""
def autoEncoder_train(X_train, X_vali, encoder_layers, decoder_layers, optimizer = 'RMSprop', loss = "mse", epoches = 2000):
    from keras.callbacks import ReduceLROnPlateau,EarlyStopping
        
    ae_model,encoder = get_autoEncoder(X_train.shape[1], encoder_layers, decoder_layers, optimizer, loss)
    reduce_lr = ReduceLROnPlateau(patience = 15)
    early_stopping = EarlyStopping(patience = 50)
    
    history = ae_model.fit(X_train, X_train, nb_epoch=epoches, callbacks=[reduce_lr, early_stopping],
                           validation_data = [X_vali, X_vali])
    print(history)
    print('$statistic-log,module=refactor,platform=XQUANT-Cloud')
    return ae_model, encoder