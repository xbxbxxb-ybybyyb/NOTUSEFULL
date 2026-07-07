
# coding: utf-8

# In[ ]:


import os
#get_ipython().system('wget https://github.com/ChanCheeKean/datasets/blob/main/compressed/hourly_electricity.zip?raw=true')
#get_ipython().system('unzip hourly_electricity.zip?raw=true')
#get_ipython().system('pip install pytorch_forecasting')

#os.system('wget https://github.com/ChanCheeKean/datasets/blob/main/compressed/hourly_electricity.zip?raw=true')
#os.system('unzip hourly_electricity.zip?raw=true')
#os.system('pip install pytorch_forecasting')

# In[1]:


import math
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
import torch.nn.functional as F


# # 1) Deep Transformer Model
# 
# https://towardsdatascience.com/how-to-make-a-pytorch-transformer-for-time-series-forecasting-69e073d4061e

# ## 1.1 Masking
# 
# * **Padding masking**. When using sequences of different lengths (sentences would normally be of different lengths), sequences shorter than the selected maximum sequence length (this is a hyperparameter than can have any value, e.g. 50) will be padded with a padding token. The padding tokens must be masked to prevent the model from attending to these tokens.
# 
# * **Decoder input masking** (aka “look ahead masking”). This type of masking prevents the decoder from attending to future tokens when it “considers” what “meaning” token t has.

# In[6]:


### generate mask
def generate_square_subsequent_mask(dim1: int, dim2: int):
    return torch.triu(torch.ones(dim1, dim2) * float('-inf'), diagonal=1)

### process data
def get_src_trg(
    sequence: torch.Tensor, 
    enc_seq_len: int, 
    target_seq_len: int
    ):

    """
    Generate the src (encoder input), trg (decoder input) and trg_y (the target)
    sequences from a sequence. 
    Args:
        sequence: tensor, a 1D tensor of length n where n = encoder input length + target sequence length  
        enc_seq_len: int, the desired length of the input to the transformer encoder
        target_seq_len: int, the desired length of the target sequence
    Return: 
        src: tensor, 1D, used as input to the transformer model
        trg: tensor, 1D, used as input to the transformer model
        trg_y: tensor, 1D, the target sequence against which the model output
            is compared when computing loss. 
    
    """
    # encoder input
    src = sequence[:, :enc_seq_len] 
    
    # decoder input. it must have the same dimension as the target sequence
    # values of trg_y except the last (i.e. it must be shifted right by 1)
    trg = sequence[:, enc_seq_len - 1 : sequence.size(1) - 1]
    trg = trg[:, :, 0]
    
    # The target sequence against which the model output will be compared to compute loss
    trg_y = sequence[:, -target_seq_len:]

    # to consist of the target variable not any potential exogenous variables
    trg_y = trg_y[:, :, 0]

    # # change size from [batch_size, target_seq_len, num_features] to [batch_size, target_seq_len] 
    return src, trg.unsqueeze(-1), trg_y.unsqueeze(-1)

### testing, num feature = 1
src, trg, trg_y = get_src_trg(
    sequence=torch.rand(62, 15, 1),
    enc_seq_len=10, 
    target_seq_len=5
    )

print(f"src Size: {src.size()}")
print(f"trg Size: {trg.size()}")
print(f"trg_y Size: {trg_y.size()}")


# In[5]:


class PositionalEncoder(nn.Module):
    def __init__(
        self, 
        dropout: float=0.1, 
        max_seq_len: int=5000, 
        d_model: int=512,
        ):

        super().__init__()
        self.d_model = d_model
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(max_seq_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(1, max_seq_len, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Tensor, shape [batch_size, enc_seq_len, dim_val] or 
               [enc_seq_len, batch_size, dim_val]
        """
        # pe.size = (1, 5000, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

### testing
pos_embedder = PositionalEncoder()
batch_size, seq_len, d_model = 32, 10, 512
result = pos_embedder(torch.rand(batch_size, seq_len, d_model))
print(f"Result Size: {result.size()}")


# In[10]:


class TimeSeriesTransformer(nn.Module):

    def __init__(self, 
        input_size: int,
        dec_seq_len: int,
        dim_val: int=512,  
        n_encoder_layers: int=4,
        n_decoder_layers: int=4,
        n_heads: int=8,
        dropout_encoder: float=0.2, 
        dropout_decoder: float=0.2,
        dropout_pos_enc: float=0.1,
        dim_feedforward_encoder: int=2048,
        dim_feedforward_decoder: int=2048,
        num_predicted_features: int=1
        ): 

        """
        Args:
            input_size: int, number of input variables. 1 if univariate.
            dec_seq_len: int, the length of the input sequence fed to the decoder
            dim_val: int, aka d_model.
            n_encoder_layers: int, number of stacked encoder layers in the encoder
            n_decoder_layers: int, number of stacked encoder layers in the decoder
            n_heads: int, the number of attention heads (aka parallel attention layers)
            dropout_encoder: float, the dropout rate of the encoder
            dropout_decoder: float, the dropout rate of the decoder
            dropout_pos_enc: float, the dropout rate of the positional encoder
            dim_feedforward_encoder: int, #neurons in the middle linear layer of the encoder
            dim_feedforward_decoder: int, #neurons in the middle linear layer of the decoder
            num_predicted_features: int, the number of features you want to predict.
                                    Most of the time, this will be 1 because we're
                                    only forecasting FCR-N prices in DK2, but in
                                    we wanted to also predict FCR-D with the same
                                    model, num_predicted_features should be 2.
        """

        super().__init__() 
        # the length of the input sequence fed to the decoder
        self.dec_seq_len = dec_seq_len

        # Creating the three linear layers needed for the model
        self.encoder_linear = nn.Linear(
            in_features=input_size, 
            out_features=dim_val)
        
        self.decoder_linear = nn.Linear(
            in_features=num_predicted_features,
            out_features=dim_val)  
        
        self.linear_mapping = nn.Linear(
            in_features=dim_val, 
            out_features=num_predicted_features)

        # Create positional encoder
        self.positional_encoding_layer = PositionalEncoder(
            d_model=dim_val,
            dropout=dropout_pos_enc)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=dim_val, 
            nhead=n_heads,
            dim_feedforward=dim_feedforward_encoder,
            dropout=dropout_encoder,
            batch_first=True
            )

        # Stack the encoder layers in nn.TransformerDecoder
        self.encoder = nn.TransformerEncoder(
            encoder_layer=encoder_layer,
            num_layers=n_encoder_layers, 
            norm=None
            )

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=dim_val,
            nhead=n_heads,
            dim_feedforward=dim_feedforward_decoder,
            dropout=dropout_decoder,
            batch_first=True
            )

        self.decoder = nn.TransformerDecoder(
            decoder_layer=decoder_layer,
            num_layers=n_decoder_layers, 
            norm=None
            )

    def forward(
        self, 
        src: torch.Tensor, 
        tgt: torch.Tensor, 
        src_mask: torch.Tensor=None, 
        tgt_mask: torch.Tensor=None
        ) -> torch.Tensor:

        """
        Returns a tensor of shape:
        [target_sequence_length, batch_size, num_predicted_features]
        
        Args:
            src: the encoder's output sequence. Shape: (m, S, E) where S is the source sequence length, 
                 m is the batch size, and E is the number of features (1 if univariate)

            tgt: the sequence to the decoder. Shape: (m, T, E) where T is the target sequence length, 
                 m is the batch size, and E is the number of features (1 if univariate)

            src_mask: the mask for the src sequence to prevent the model from using data points

            tgt_mask: the mask for the tgt sequence to prevent the model from using data points
        """

        # [m, in_seq, num_feat] --> [m, in_seq, dim_val]
        src = self.encoder_linear(src) 
        src = self.positional_encoding_layer(src) 
        
        # Pass through all the stacked encoder layers in the encoder, mask needed if padded
        # [m, in_seq, dim_val]
        encoder_output = self.encoder(src=src)

        # Pass decoder input through decoder input layer
        # [m, out_seq, num_feat] --> [m, out_seq, dim_val]
        decoder_input = self.decoder_linear(tgt)     

        # Pass throguh decoder
        # [m, out_seq, dim_val]
        decoder_output = self.decoder(
            tgt=decoder_input,
            memory=encoder_output,
            tgt_mask=tgt_mask,
            memory_mask=src_mask
            )

        # shape [m, out_seq, num_feat]
        decoder_output = self.linear_mapping(decoder_output) 
        return decoder_output

### testing
## Model parameters
dim_val = 512 # divisible by n_heads. 512 is used in the original transformer paper.
n_heads = 8 # The number of attention heads (aka parallel attention layers)
n_decoder_layers = 4 # Number of times the decoder layer is stacked in the decoder
n_encoder_layers = 4 # Number of times the encoder layer is stacked in the encoder
input_size = 1 # The number of input variables. 1 if univariate forecasting.
dec_seq_len = 5 # length of input given to decoder.
enc_seq_len = 10 # length of input given to encoder.
output_sequence_length = 58 # Length of the target sequence, i.e. how many time steps should your forecast cover
max_seq_len = enc_seq_len # What's the longest sequence the model will encounter (for positional encoder)

### testing
model = TimeSeriesTransformer(
    dim_val=dim_val,
    input_size=input_size, 
    dec_seq_len=dec_seq_len,
    n_decoder_layers=n_decoder_layers,
    n_encoder_layers=n_encoder_layers,
    n_heads=n_heads,
    )

# Make src mask for decoder with size:
tgt_mask = generate_square_subsequent_mask(
    dim1=dec_seq_len,
    dim2=dec_seq_len
    )
src_mask = None

result = model(src, trg, src_mask, tgt_mask)
print('Result Size: ', result.size())


# In[5]:


### loss function
criterion = nn.MSELoss()
loss_value = criterion(result, trg_y)
print(loss_value)


# In[6]:


### generate prediction from inference
forecast_window = 10
test_data = src

# [m, seq_len, num_feat] --> [m] --> [m, 1, 1]
pred_token = src[:, -1, 0] 
pred_token = pred_token.unsqueeze(-1).unsqueeze(-1)
        
for _ in range(forecast_window):
    tgt_mask = generate_square_subsequent_mask(
        dim1=pred_token.size(1), dim2=pred_token.size(1)
        )
    src_mask = None

    # output grow: [m, 1, 1], [m, 2, 1], ..., [m, forecast_window, 1]
    prediction = model(src, pred_token, src_mask, tgt_mask) 

    # include only the last values
    prediction = prediction[:, -1, :].unsqueeze(1)
    pred_token = torch.cat((pred_token, prediction.detach()), 1)

final_output = pred_token[:, 1:, :]
print('Final Pred Token Size: ', pred_token.size())


# # 2) Temporal Fusion Transformer
# 
# <img src='https://raw.githubusercontent.com/KalleBylin/temporal-fusion-transformers/main/img/tft_architecture.png'></img>
# 
# https://towardsdatascience.com/temporal-fusion-transformer-googles-model-for-interpretable-time-series-forecasting-5aa17beb621
# 
# 

# ## 2.1 Pytorch Forecasting

# ### 2.1.1 Data Loading

# In[7]:


import os
from pathlib import Path
import numpy as np
import pandas as pd
import warnings
from pytorch_forecasting import Baseline, TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from pytorch_forecasting.data.examples import get_stallion_data
import pytorch_lightning as pl
from pytorch_forecasting.metrics import SMAPE, PoissonLoss, QuantileLoss


# In[ ]:


### load dataset
data = get_stallion_data()

# add time index
data["time_idx"] = data["date"].dt.year * 12 + data["date"].dt.month
data["time_idx"] -= data["time_idx"].min()

# add additional features
data["month"] = data.date.dt.month.astype(str).astype("category")
data["log_volume"] = np.log(data.volume + 1e-8)
data["avg_volume_by_sku"] = data.groupby(["time_idx", "sku"], observed=True).volume.transform("mean")
data["avg_volume_by_agency"] = data.groupby(["time_idx", "agency"], observed=True).volume.transform("mean")

# encode special days as one variable and thus need to first reverse one-hot encoding
special_days = [
    "easter_day", "good_friday", "new_year", "christmas", "labor_day",
    "independence_day", "revolution_day_memorial", "regional_games", 
    "fifa_u_17_world_cup", "football_gold_cup", "beer_capital", "music_fest",
    ]
data[special_days] = data[special_days].apply(lambda x: x.map({0: "-", 1: x.name})).astype("category")
data.sample(5)


# In[ ]:


### create dataset
max_prediction_length = 6
max_encoder_length = 24
training_cutoff = data["time_idx"].max() - max_prediction_length

training = TimeSeriesDataSet(
    data[data['time_idx'] <= training_cutoff],
    time_idx="time_idx",
    target="volume",
    group_ids=["agency", "sku"],
    min_encoder_length=max_encoder_length // 2,
    max_encoder_length=max_encoder_length,
    min_prediction_length=1,
    max_prediction_length=max_prediction_length,
    static_categoricals=["agency", "sku"],
    static_reals=["avg_population_2017", "avg_yearly_household_income_2017"],
    variable_groups={"special_days": special_days},  # group of categorical variables can be treated as one variable
    time_varying_known_categoricals=["special_days", "month"],
    time_varying_known_reals=["time_idx", "price_regular", "discount_in_percent"],
    time_varying_unknown_categoricals=[],
    time_varying_unknown_reals=[
        "volume",
        "log_volume",
        "industry_volume",
        "soda_volume",
        "avg_max_temp",
        "avg_volume_by_agency",
        "avg_volume_by_sku",
    ],
    # use softplus and normalize by group
    target_normalizer=GroupNormalizer(
        groups=["agency", "sku"], transformation="softplus"
    ), 
    add_relative_time_idx=True,
    add_target_scales=True,
    add_encoder_length=True,
)

# create validation set (predict=True) which means to predict the last max_prediction_length points in time
# for each series
validation = TimeSeriesDataSet.from_dataset(training, data, predict=True, stop_randomization=True)

# create dataloaders for model
batch_size = 128  # set this between 32 to 128
train_dataloader = training.to_dataloader(train=True, batch_size=batch_size, num_workers=0)
val_dataloader = validation.to_dataloader(train=False, batch_size=batch_size * 10, num_workers=0)


# In[ ]:


### baseline model and loss
actuals = torch.cat([y for x, (y, weight) in iter(val_dataloader)])
baseline_predictions = Baseline().predict(val_dataloader)
(actuals - baseline_predictions).abs().mean().item()


# ### 2.1.2 Training

# In[ ]:


### define trainer
trainer = pl.Trainer(
    gpus=0,
    # clipping gradients to prevent divergance of the gradient for recurrent neural networks
    gradient_clip_val=0.1,
)

tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=16,  # most important hyperparameter apart from learning rate
    attention_head_size=1, # Set to up to 4 for large datasets
    dropout=0.1,  # between 0.1 and 0.3 are good values
    hidden_continuous_size=8,  # set to <= hidden_size
    output_size=7,  # 7 quantiles by default
    loss=QuantileLoss(),
    reduce_on_plateau_patience=4, # reduce learning rate if no improvement after x epochs
)

print(f"Number of parameters in network: {tft.size() / 1e3:.1f}k")


# In[ ]:


trainer.fit(
    tft,
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
)


# ### 2.1.3 Evaluation

# In[ ]:


# calcualte mean absolute error on validation set
best_model_path = trainer.checkpoint_callback.best_model_path
best_tft = TemporalFusionTransformer.load_from_checkpoint(best_model_path)

actuals = torch.cat([y[0] for x, y in iter(val_dataloader)])
predictions = best_tft.predict(val_dataloader)
(actuals - predictions).abs().mean()


# In[ ]:


raw_predictions, x = best_tft.predict(val_dataloader, mode="raw", return_x=True)

for idx in range(10):  # plot 10 examples
    best_tft.plot_prediction(x, raw_predictions, idx=idx, add_loss_to_title=True);
    break


# ### 2.1.4 Interpretation

# In[ ]:


interpretation = best_tft.interpret_output(raw_predictions, reduction="sum")
best_tft.plot_interpretation(interpretation)


# In[ ]:


dependency = best_tft.predict_dependency(
    val_dataloader.dataset, "discount_in_percent", np.linspace(0, 30, 30), show_progress_bar=True, mode="dataframe"
)


# In[ ]:


# plotting median and 25% and 75% percentile
agg_dependency = dependency.groupby("discount_in_percent").normalized_prediction.agg(
    median="median", q25=lambda x: x.quantile(0.25), q75=lambda x: x.quantile(0.75)
)
ax = agg_dependency.plot(y="median")
ax.fill_between(agg_dependency.index, agg_dependency.q25, agg_dependency.q75, alpha=0.3);


# ## 2.2 Building From Scratch
# 
# <img src='https://raw.githubusercontent.com/KalleBylin/temporal-fusion-transformers/main/img/tft_architecture.png'></img>
# 
# https://github.com/KalleBylin/temporal-fusion-transformers/blob/main/Temporal%20Fusion%20Transformer.ipynb

# ### 2.2.1 CONFIG

# In[5]:


input_columns = [
    "power_usage", "days_from_start", "hours_from_start", 
    "categorical_day_of_week", "categorical_hour", "month", "categorical_id"
    ]

target_column = "power_usage"
entity_column = "categorical_id"
time_column = "date"
col_to_idx = {col: idx for idx, col in enumerate(input_columns)}

params = {
    "quantiles": [0.1, 0.5, 0.9],
    "batch_size": 64,
    "dropout": 0.3,
    "device": "cuda",
    "hidden_layer_size": 128,
    "num_lstm_layers": 1,
    "embedding_dim": 8,
    "encoder_steps": 252,
    "num_attention_heads": 1, 
    "col_to_idx": col_to_idx, 
    "static_covariates": ["categorical_id"], 
    "time_dependent_categorical": ["categorical_day_of_week", "categorical_hour", "month"], 
    "time_dependent_continuous": ['power_usage', 'days_from_start', "hours_from_start",], 
    "category_nunique": {
        "categorical_day_of_week": 7, 
        "categorical_hour": 24, 
        "month": 9, 
        "categorical_id": 369, 
        }, 
    # known future variable
    "known_time_dependent": [
        "categorical_day_of_week", "categorical_hour", "month", 
        "days_from_start", "hours_from_start"
        ],
    # unknown future variable
    "observed_time_dependent": ["power_usage"]
}


# ### 2.2.2 Data Loading

# In[4]:


df = pd.read_csv('hourly_electricity.csv')
df.head()


# In[ ]:


train = raw_data[raw_data['year'] < 2016]
valid = raw_data.loc[(raw_data['year'] >= 2016) & (raw_data['year'] < 2018)]
test = raw_data.loc[(raw_data['year'] >= 2018) & (raw_data.index <= '2019-06-28')]


# In[ ]:


real_columns = ['log_vol', 'open_to_close', 'days_from_start']
categorical_columns = ['Symbol', 'day_of_week', 'day_of_month', 'week_of_year', 'month', 'Region']


def fit_preprocessing(train, real_columns, categorical_columns):
    real_scalers = StandardScaler().fit(train[real_columns].values)

    categorical_scalers = {}
    num_classes = []
    for col in categorical_columns:
        srs = train[col].apply(str) 
        categorical_scalers[col] = LabelEncoder().fit(srs.values)
        num_classes.append(srs.nunique())

    return real_scalers, categorical_scalers


def transform_inputs(df, real_scalers, categorical_scalers, real_columns, categorical_columns):
    out = df.copy()
    out[real_columns] = real_scalers.transform(df[real_columns].values)

    for col in categorical_columns:
        string_df = df[col].apply(str)
        out[col] = categorical_scalers[col].transform(string_df)

    return out


real_scalers, categorical_scalers = fit_preprocessing(train, real_columns, categorical_columns)
train = transform_inputs(train, real_scalers, categorical_scalers, real_columns, categorical_columns)
valid = transform_inputs(valid, real_scalers, categorical_scalers, real_columns, categorical_columns)
test = transform_inputs(test, real_scalers, categorical_scalers, real_columns, categorical_columns)


# In[ ]:


class TFT_Dataset(Dataset):
    def __init__(self, data, entity_column, time_column, target_column, 
                 input_columns, encoder_steps, decoder_steps):
        """
          data (pd.DataFrame): dataframe containing raw data
          entity_column (str): name of column containing entity data
          time_column (str): name of column containing date data
          target_column (str): name of column we need to predict
          input_columns (list): list of string names of columns used as input
          encoder_steps (int): number of known past time steps used for forecast. Equivalent to size of LSTM encoder
          decoder_steps (int): number of input time steps used for each forecast date. Equivalent to the width N of the decoder
        """
        
        self.encoder_steps = encoder_steps
             
        inputs = []
        outputs = []
        entity = []
        time = []

        for e in train[entity_column].unique():
          entity_group = data[data[entity_column]==e]
          
          data_time_steps = len(entity_group)

          if data_time_steps >= decoder_steps:
            x = entity_group[input_columns].values.astype(np.float32)
            inputs.append(np.stack([x[i:data_time_steps - (decoder_steps - 1) + i, :] for i in range(decoder_steps)], axis=1))

            y = entity_group[[target_column]].values.astype(np.float32)
            outputs.append(np.stack([y[i:data_time_steps - (decoder_steps - 1) + i, :] for i in range(decoder_steps)], axis=1))

            e = entity_group[[entity_column]].values.astype(np.float32)
            entity.append(np.stack([e[i:data_time_steps - (decoder_steps - 1) + i, :] for i in range(decoder_steps)], axis=1))

            t = entity_group[[time_column]].values.astype(np.int64)
            time.append(np.stack([t[i:data_time_steps - (decoder_steps - 1) + i, :] for i in range(decoder_steps)], axis=1))

        self.inputs = np.concatenate(inputs, axis=0)
        self.outputs = np.concatenate(outputs, axis=0)[:, encoder_steps:, :]
        self.entity = np.concatenate(entity, axis=0)
        self.time = np.concatenate(time, axis=0)
        self.active_inputs = np.ones_like(outputs)

        self.sampled_data = {
            'inputs': self.inputs,
            'outputs': self.outputs[:, self.encoder_steps:, :],
            'active_entries': np.ones_like(self.outputs[:, self.encoder_steps:, :]),
            'time': self.time,
            'identifier': self.entity
        }
        
    def __getitem__(self, index):
        s = {
        'inputs': self.inputs[index],
        'outputs': self.outputs[index], 
        'active_entries': np.ones_like(self.outputs[index]), 
        'time': self.time[index],
        'identifier': self.entity[index]
        }

        return s

    def __len__(self):
        return self.inputs.shape[0]

training_data = TFT_Dataset(train, entity_column, time_column, target_column, input_columns, ENCODER_STEPS, DECODER_STEPS)
#validation_data = TFT_Dataset(valid, entity_column, time_column, target_column, input_columns, ENCODER_STEPS, DECODER_STEPS)
testing_data = TFT_Dataset(test, entity_column, time_column, target_column, input_columns, ENCODER_STEPS, DECODER_STEPS)

train_dataloader = DataLoader(training_data, batch_size=BATCH_SIZE, num_workers=2, shuffle=False)
# valid_dataloader = DataLoader(validation_data, batch_size=BATCH_SIZE, num_workers=2, shuffle=False)
test_dataloader = DataLoader(testing_data, batch_size=BATCH_SIZE, num_workers=2, shuffle=False)


# ### 2.2.3 Gated Linear Unit & Gated Residual Network
# 
# Gated Residual Network blocks are among the main basic components of this network. They enable efficient information flow along with the skip connections and gating layers. The mechanisms allow the network to adapt both depth and complexity in order to perform well on a wide range of datasets and tasks.
# 
# * **Gated Linear Unit**. It is hard to know which variables are actually relevant for the prediction task from the outset. The gates of the Gated Linear Unit make it possible to suppress parts of the architecture that are not necessary in a particular scneario or with a specific dataset.
# 
# * **Temporal Layer** A wrapper that makes it possible to apply a layer to every temporal slice of an input. For example, it can be used to apply the same instance of a convolutional layer with the same set of weights on each timestep in the data. This TemporalLayer tries to collapse the tensor before passing it through the layer and then rebuilding the original shape before returning the resulting tensor.
# 
# * **Gated Residual Network** is a flexible block that can apply non-linear processing when required. The Gated Linear Unit defined above helps the GRN how much to contribute to its input and could potentially skip the layer altogether if necessary. GLU outputs close to 0 would supreess the non-linear contribution.

# In[31]:


class GLU(nn.Module):
    """
      The Gated Linear Unit GLU(a, b) = mult(a,sigmoid(b)). 
      Sigmoid(b) corresponds to a gate that controls 
      what information from a is passed to the following layer. 

      Args:
          input_size (int): number defining input and output size of the gate
    """
    def __init__(self, input_size):
        super().__init__()
        
        self.a = nn.Linear(input_size, input_size)
        self.sigmoid = nn.Sigmoid()
        self.b = nn.Linear(input_size, input_size)
        
    def forward(self, x):
        """
        Args:
            x (torch.tensor): tensor passing through the gate
        """
        gate = self.sigmoid(self.b(x))
        x = self.a(x)
        return torch.mul(gate, x)

class TemporalLayer(nn.Module):
    def __init__(self, module):
        super().__init__()
        """
        Collapses input of dim T*N*H to (T*N)*H, and applies to a module.
        Allows handling of variable sequence lengths and minibatch sizes.
        """
        self.module = module

    def forward(self, x):
        """
        Args:
            x (torch.tensor): tensor with time steps to pass through the same layer.
        """
        t, n = x.size(0), x.size(1)
        x = x.reshape(t * n, -1)
        x = self.module(x)
        x = x.reshape(t, n, x.size(-1))
        return x

class GatedResidualNetwork(nn.Module):
    """
      The Gated Residual Network gives the model flexibility to apply non-linear
      processing only when needed. It is difficult to know beforehand which
      variables are relevant and in some cases simpler models can be beneficial.

      GRN(a, c) = LayerNorm(a + GLU(eta_1))
      eta_1 = W_1*eta_2 + b_1
      eta_2 = ELU(W_2*a + W_3*c + b_2)
      
      Args:
          input_size (int): Size of the input
          hidden_size (int): Size of the hidden layer
          output_size (int): Size of the output layer
          dropout (float): Fraction between 0 and 1 corresponding to the degree of dropout used
          context_size (int): Size of the static context vector
          is_temporal (bool): Flag to decide if TemporalLayer has to be used or not
    """
    def __init__(
        self, 
        input_size, 
        hidden_size, 
        output_size, 
        dropout, 
        context_size=None, 
        is_temporal=True
        ):

        super().__init__()

        self.input_size = input_size
        self.output_size = output_size
        self.context_size = context_size
        self.hidden_size = hidden_size
        self.dropout = dropout
        self.is_temporal = is_temporal
        
        if self.is_temporal:
            if self.input_size != self.output_size:
                self.skip_layer = TemporalLayer(nn.Linear(self.input_size, self.output_size))

            # Context vector c
            if self.context_size != None:
                self.c = TemporalLayer(nn.Linear(self.context_size, self.hidden_size, bias=False))

            # Dense & ELU
            self.dense1 = TemporalLayer(nn.Linear(self.input_size, self.hidden_size))
            self.elu = nn.ELU()

            # Dense & Dropout
            self.dense2 = TemporalLayer(nn.Linear(self.hidden_size,  self.output_size))
            self.dropout = nn.Dropout(self.dropout)

            # Gate, Add & Norm
            self.gate = TemporalLayer(GLU(self.output_size))
            self.layer_norm = TemporalLayer(nn.BatchNorm1d(self.output_size))

        else:
            if self.input_size != self.output_size:
                self.skip_layer = nn.Linear(self.input_size, self.output_size)

            # Context vector c
            if self.context_size != None:
                self.c = nn.Linear(self.context_size, self.hidden_size, bias=False)

            # Dense & ELU
            self.dense1 = nn.Linear(self.input_size, self.hidden_size)
            self.elu = nn.ELU()

            # Dense & Dropout
            self.dense2 = nn.Linear(self.hidden_size,  self.output_size)
            self.dropout = nn.Dropout(self.dropout)

            # Gate, Add & Norm
            self.gate = GLU(self.output_size)
            self.layer_norm = nn.BatchNorm1d(self.output_size)

    def forward(self, x, c=None):
        """
        Args:
            x (torch.tensor): tensor thas passes through the GRN
            c (torch.tensor): Optional static context vector
        """

        if self.input_size != self.output_size:
            a = self.skip_layer(x)
            print("test: ", a.size())
        else:
            a = x
        
        x = self.dense1(x)

        if c != None:
            c = self.c(c.unsqueeze(1))
            x += c

        eta_2 = self.elu(x)
        
        eta_1 = self.dense2(eta_2)
        eta_1 = self.dropout(eta_1)

        gate = self.gate(eta_1)
        gate += a
        x = self.layer_norm(gate)
        
        return x


# ### 2.2.4 Variable Selection Network
# 
# ![image.png](data:image/png;base64,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)
# 
# **Observed inputs** are time dependent variables that are known only up until t, point where forecasting of target starts. **Known inputs** are time dependent variables that can be known ahead of time (e.g. holidays, special events)
# 
# The Variable Selection Network makes it possible for the model to eliminate the noise raised from so many variables. It evaluates the most important variables for interpretability of the trained model.

# In[32]:


class VariableSelectionNetwork(nn.Module):
    """
      The variable selection weights are created by feeding both the flattened
      vector of all past inputs at time t (E_t) and an optional context vector 
      through a GRN, followed by a Softmax layer.

      V_xt = Softmax(GRN_v(E_t, c_s)) 

      Also, the feature vector for each variable is fed through its 
      own GRN to create an additional layer of non-linear processing.

      Processed features are then weighted by the variable selection weights
      and combined.

      Args:
          input_size (int): Size of the input
          output_size (int): Size of the output layer
          hidden_size (int): Size of the hidden layer
          dropout (float): Fraction between 0 and 1 corresponding to the degree of dropout used
          context_size (int): Size of the static context vector
          is_temporal (bool): Flag to decide if TemporalLayer has to be used or not
    """

    def __init__(
        self, 
        input_size: int, 
        output_size: int, 
        hidden_size: int, 
        dropout: float, 
        context_size: int=None,
        is_temporal: bool=True
        ):

        super().__init__()

        self.hidden_size = hidden_size
        self.input_size = input_size
        self.output_size = output_size
        self.dropout = dropout
        self.context_size = context_size
        self.is_temporal = is_temporal
       
        self.flattened_inputs = GatedResidualNetwork(
            self.output_size*self.input_size, 
            self.hidden_size, self.output_size, 
            self.dropout, 
            self.context_size, 
            self.is_temporal
        )
        
        self.transformed_inputs = nn.ModuleList(
            [
                GatedResidualNetwork(
                    self.input_size, 
                    self.hidden_size, 
                    self.hidden_size, 
                    self.dropout, 
                    self.context_size, 
                    self.is_temporal
                    ) for i in range(self.output_size)
                ])

        self.softmax = nn.Softmax(dim=-1)

    def forward(self, embedding, context=None):
        """
        Args:
          embedding (torch.tensor): Entity embeddings for categorical variables and linear 
                                    transformations for continuous variables.
          context (torch.tensor): obtained from a static covariate encoder and omitted 
                                  for static variables
        """

        # Generation of variable selection weights
        sparse_weights = self.flattened_inputs(embedding, context)

        if self.is_temporal:
            sparse_weights = self.softmax(sparse_weights).unsqueeze(2)
        else:
            sparse_weights = self.softmax(sparse_weights).unsqueeze(1)

        # Additional non-linear processing for each feature vector
        transformed_embeddings = torch.stack(
            [
                self.transformed_inputs[i](
                    embedding[Ellipsis, i*self.input_size:(i+1)*self.input_size]
                    ) for i in range(self.output_size)
                ], 
            axis=-1)

        # Processed features are weighted by their corresponding weights and combined
        combined = transformed_embeddings * sparse_weights
        combined = combined.sum(axis=-1)

        return combined, sparse_weights


# ### 2.2.5 Interpretable Multi-Head Attention
# 
# This particular block is used to learn long-term relationships from observed time-varying inputs. It is a modified version of the more general multi-head attention block used in transformer-based architectures, in order to improve explainability. It is well-known that the dot-product is a very simple but powerful tool to evaluate similarity between two vectors. For this same reason, it is also a great tool to help our model know what parts of the inputs to focus on based on the keys and queries. The scaling factor helps improve the performance of dot product attention by not allowing the softmax to move into regions with very small gradients.
# 
# Multi-head attention allows us to compute multiple attention computations in parallel on different projections of the keys, queries and values. This makes it possible for the model to leverage different types of information in the input which would otherwise be lost by the averaging effect in a single attention head. The original version fails in allowing us to be able to interpret the importance of each feature. The TFT proposes a modification of multi-head attention such that there are shared value weights among the different heads with an additive aggregation of the heads for better interpretability.
# 
# 

# In[33]:


class ScaledDotProductAttention(nn.Module):
    """
    Attention mechansims usually scale values based on relationships between
    keys and queries. 
    
    Attention(Q,K,V) = A(Q,K)*V where A() is a normalization function.

    A common choice for the normalization function is scaled dot-product attention:

    A(Q,K) = Softmax(Q*K^T / sqrt(d_attention))

    Args:
          dropout (float): Fraction between 0 and 1 corresponding to the degree of dropout used
    """
    def __init__(self, dropout=0.0):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.softmax = nn.Softmax(dim=2)
        
    def forward(self, query, key, value, mask=None):
        """
        Args:
          query (torch.tensor): 
          key (torch.tensor):
          value (torch.tensor): 
          mask (torch.tensor):
        """

        d_k = key.shape[-1]
        scaling_factor = torch.sqrt(torch.tensor(d_k).to(torch.float32))
        scaled_dot_product = torch.matmul(query, key.permute(0,2,1)) / scaling_factor 
        if mask != None:
            scaled_dot_product = scaled_dot_product.masked_fill(mask == 0, -1e9)
        attention = self.softmax(scaled_dot_product)
        attention = self.dropout(attention)
        output = torch.matmul(attention, value)

        return output, attention

class InterpretableMultiHeadAttention(nn.Module):
    """
    Different attention heads can be used to improve the learning capacity of 
    the model. 

    MultiHead(Q,K,V) = [H_1, ..., H_m]*W_H
    H_h = Attention(Q*Wh_Q, K*Wh_K, V*Wh_V)

    Each head has specific weights for keys, queries and values. W_H linearly
    combines the concatenated outputs from all heads.

    To increase interpretability, multi-head attention has been modified to share
    values in each head.

    InterpretableMultiHead(Q,K,V) = H_I*W_H
    H_I = 1/H * SUM(Attention(Q*Wh_Q, K*Wh_K, V*W_V)) # Note that W_V does not depend on the head. 

    Args:
          num_heads (int): Number of attention heads
          hidden_size (int): Hidden size of the model
          dropout (float): Fraction between 0 and 1 corresponding to the degree of dropout used
    """
    def __init__(self, hidden_size, num_attention_heads, dropout=0.0):
        super().__init__()

        self.num_attention_heads = num_attention_heads
        self.hidden_size = hidden_size
        self.dropout = nn.Dropout(dropout)

        self.qs = nn.ModuleList(
            [
                nn.Linear(self.hidden_size, self.hidden_size, bias=False) 
                for i in range(self.num_attention_heads)
                ])
        
        self.ks = nn.ModuleList(
            [
                nn.Linear(self.hidden_size, self.hidden_size, bias=False) 
                for i in range(self.num_attention_heads)
                ])
        
        # Value is shared for improved interpretability
        vs_layer = nn.Linear(self.hidden_size, self.hidden_size, bias=False) 
        self.vs = nn.ModuleList([vs_layer for i in range(self.num_attention_heads)])
        self.attention = ScaledDotProductAttention()
        self.linear = nn.Linear(self.hidden_size, self.hidden_size, bias=False)

    def forward(self, query, key, value, mask=None):
        
        batch_size, tgt_len, embed_dim = query.shape
        head_dim = embed_dim // self.num_attention_heads

        # Now we iterate over each head to calculate outputs and attention
        heads = []
        attentions = []

        for i in range(self.num_attention_heads):
            q_i = self.qs[i](query)
            k_i = self.ks[i](key)
            v_i = self.vs[i](value)

            # Reshape q, k, v for multihead attention
            q_i = query                .reshape(batch_size, tgt_len, self.num_attention_heads, head_dim)                .transpose(1,2)                .reshape(batch_size*self.num_attention_heads, tgt_len, head_dim)

            k_i = key                .reshape(batch_size, tgt_len, self.num_attention_heads, head_dim)                .transpose(1,2)                .reshape(batch_size*self.num_attention_heads, tgt_len, head_dim)

            v_i = value                .reshape(batch_size, tgt_len, self.num_attention_heads, head_dim)                .transpose(1,2)                .reshape(batch_size*self.num_attention_heads, tgt_len, head_dim)

            head, attention = self.attention(q_i, k_i, v_i, mask)

            # Revert to original target shape
            head = head.reshape(batch_size, self.num_attention_heads, tgt_len, head_dim)                .transpose(1,2)                .reshape(-1, tgt_len, self.num_attention_heads*head_dim)
                
            head_dropout = self.dropout(head)
            heads.append(head_dropout)
            attentions.append(attention)

        # Output the results
        if self.num_attention_heads > 1:
            heads = torch.stack(heads, dim=2) #.reshape(batch_size, tgt_len, -1, self.hidden_size)
            outputs = torch.mean(heads, dim=2)
        else:
            outputs = head

        attentions = torch.stack(attentions, dim=2)
        attention = torch.mean(attentions, dim=2)
        
        outputs = self.linear(outputs)
        outputs = self.dropout(outputs)

        return outputs, attention


# ### 2.2.6 TFT Architecture

# In[38]:


class TemporalFusionTransformer(nn.Module):
    def __init__(self, parameters):

        super().__init__()

        # Inputs
        self.col_to_idx = parameters["col_to_idx"]
        self.static_covariates = parameters["static_covariates"] 
        self.time_dependent_categorical = parameters["time_dependent_categorical"]
        self.time_dependent_continuous = parameters["time_dependent_continuous"]
        self.category_nunique = parameters["category_nunique"]
        self.known_time_dependent = parameters["known_time_dependent"]
        self.observed_time_dependent = parameters["observed_time_dependent"]
        self.time_dependent = self.known_time_dependent + self.observed_time_dependent

        # Model Parameter
        self.batch_size = parameters['batch_size']
        self.encoder_steps = parameters['encoder_steps']
        self.hidden_size = parameters['hidden_layer_size']
        self.num_lstm_layers = parameters['num_lstm_layers']
        self.dropout = parameters['dropout']
        self.embedding_dim = parameters['embedding_dim']
        self.num_attention_heads = parameters['num_attention_heads']

        # Outputs
        self.quantiles = parameters['quantiles']
        self.device = parameters['device']

        # embeddings for the static covariates and static context vectors
        self.static_embeddings = nn.ModuleDict(
            {
                col: nn.Embedding(self.category_nunique[col], self.embedding_dim) 
                for col in self.static_covariates
             }) 
        
        self.static_variable_selection = VariableSelectionNetwork(
            self.embedding_dim, 
            len(self.static_covariates), 
            self.hidden_size, 
            self.dropout, 
            is_temporal=False
        ) 

        self.static_context_variable_selection = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout, 
            is_temporal=False
        )
        
        self.static_context_enrichment = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout, 
            is_temporal=False
            )
        
        self.static_context_state_h = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout, 
            is_temporal=False
            )
        
        self.static_context_state_c = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout, 
            is_temporal=False
            )
        
        # Prepare embeddings and linear transformations for time dependent variables
        self.temporal_cat_embeddings = nn.ModuleDict(
            {
                col: TemporalLayer(
                    nn.Embedding(self.category_nunique[col], self.embedding_dim)
                    ) for col in self.time_dependent_categorical
             })
        
        self.temporal_real_transformations = nn.ModuleDict(
            {
                col: TemporalLayer(
                    nn.Linear(1, self.embedding_dim)
                    ) for col in self.time_dependent_continuous
             })

        # Variable selection and encoder for past inputs
        self.past_variable_selection = VariableSelectionNetwork(
            self.embedding_dim, 
            len(self.time_dependent), 
            self.hidden_size, 
            self.dropout, 
            context_size=self.hidden_size
            )

        # Variable selection and decoder for known future inputs
        self.future_variable_selection = VariableSelectionNetwork(
            self.embedding_dim, 
            len([col for col in self.time_dependent if col not in self.observed_time_dependent]), 
            self.hidden_size, 
            self.dropout, 
            context_size=self.hidden_size
            )

        # LSTM encoder and decoder
        self.lstm_encoder = nn.LSTM(
            input_size=self.hidden_size, 
            hidden_size=self.hidden_size, 
            num_layers=self.num_lstm_layers, 
            dropout=self.dropout
            )
        
        self.lstm_decoder = nn.LSTM(
            input_size=self.hidden_size, 
            hidden_size=self.hidden_size, 
            num_layers=self.num_lstm_layers, 
            dropout=self.dropout
            )

        # Gated skip connection and normalization
        self.gated_skip_connection = TemporalLayer(GLU(self.hidden_size))
        self.add_norm = TemporalLayer(nn.BatchNorm1d(self.hidden_size))

        # Temporal Fusion Decoder
        # Static enrichment layer
        self.static_enrichment = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout, 
            self.hidden_size
            )
        
        # Temporal Self-attention layer
        self.multihead_attn = InterpretableMultiHeadAttention(
            self.num_attention_heads, 
            self.hidden_size
            )
        
        self.attention_gated_skip_connection = TemporalLayer(GLU(self.hidden_size))
        self.attention_add_norm = TemporalLayer(nn.BatchNorm1d(self.hidden_size, self.hidden_size))

        # Position-wise feed-forward layer
        self.position_wise_feed_forward = GatedResidualNetwork(
            self.hidden_size, 
            self.hidden_size, 
            self.hidden_size, 
            self.dropout
            )

        # Output layer
        self.output_gated_skip_connection = TemporalLayer(GLU(self.hidden_size))
        self.output_add_norm = TemporalLayer(nn.BatchNorm1d(self.hidden_size, self.hidden_size))
        self.output = TemporalLayer(nn.Linear(self.hidden_size, len(self.quantiles)))
        
    def define_static_covariate_encoders(self, x):
        embedding_vectors = [
            self.static_embeddings[col](x[:, 0, self.col_to_idx[col]].long().to(self.device)) 
            for col in self.static_covariates
            ]
            
        static_embedding = torch.cat(embedding_vectors, dim=1)
        static_encoder, static_weights = self.static_variable_selection(static_embedding)

        # Static context vectors
        # temporal variable selection
        static_context_s = self.static_context_variable_selection(static_encoder) 
        # static enrichment layer
        static_context_e = self.static_context_enrichment(static_encoder) 
        # local processing of temporal features (encoder/decoder)
        static_context_h = self.static_context_state_h(static_encoder) 
        # local processing of temporal features (encoder/decoder)
        static_context_c = self.static_context_state_c(static_encoder) 

        return (
            static_encoder, static_weights, static_context_s, 
            static_context_e, static_context_h, static_context_c)

    def define_past_inputs_encoder(self, x, context):
        embedding_vectors = torch.cat(
            [
                self.temporal_cat_embeddings[col](x[:, :, self.col_to_idx[col]].long()) 
                    for col in self.time_dependent_categorical
             ], dim=2)
        
        transformation_vectors = torch.cat(
            [
                self.temporal_real_transformations[col](x[:, :, self.col_to_idx[col]]) 
                    for col in self.time_dependent_continuous
             ], dim=2)

        past_inputs = torch.cat([embedding_vectors, transformation_vectors], dim=2)
        past_encoder, past_weights = self.past_variable_selection(past_inputs, context)

        return past_encoder.transpose(0, 1), past_weights

    def define_known_future_inputs_decoder(self, x, context):
        embedding_vectors = torch.cat(
            [
                self.temporal_cat_embeddings[col](x[:, :, self.col_to_idx[col]].long()) 
                    for col in self.time_dependent_categorical if col not in self.observed_time_dependent
             ], dim=2)
        
        transformation_vectors = torch.cat(
            [
                self.temporal_real_transformations[col](x[:, :, self.col_to_idx[col]]) 
                    for col in self.time_dependent_continuous if col not in self.observed_time_dependent
             ], dim=2)

        future_inputs = torch.cat([embedding_vectors, transformation_vectors], dim=2)
        future_decoder, future_weights = self.future_variable_selection(future_inputs, context)

        return future_decoder.transpose(0, 1), future_weights

    def define_lstm_encoder(self, x, static_context_h, static_context_c):
        output, (state_h, state_c) = self.lstm_encoder(
            x, 
            (
                static_context_h.unsqueeze(0).repeat(self.num_lstm_layers,1,1), 
                static_context_c.unsqueeze(0).repeat(self.num_lstm_layers,1,1)
                ),
            )
        
        return output, state_h, state_c

    def define_lstm_decoder(self, x, state_h, state_c):
        output, (_, _) = self.lstm_decoder(
            x, 
            (
                state_h.unsqueeze(0).repeat(self.num_lstm_layers,1,1), 
             state_c.unsqueeze(0).repeat(self.num_lstm_layers,1,1)
             )
            )
        
        return output

    def get_mask(self, attention_inputs):
        mask = torch.cumsum(
            torch.eye(
                attention_inputs.shape[0]*self.num_attention_heads, 
                attention_inputs.shape[1]
                ), 
            dim=1
            )

        return mask.unsqueeze(2).to(self.device)

    def forward(self, x):

        # Static variable selection and static covariate encoders
        static_encoder, static_weights, static_context_s, static_context_e, static_context_h, static_context_c = self.define_static_covariate_encoders(x["inputs"])

        # Past input variable selection and LSTM encoder
        past_encoder, past_weights = self.define_past_inputs_encoder(
            x["inputs"][:, :self.encoder_steps, :].float().to(self.device), 
            static_context_s
            )

        # Known future inputs variable selection and LSTM decoder
        future_decoder, future_weights = self.define_known_future_inputs_decoder(
            x["inputs"][:, self.encoder_steps:, :].float().to(self.device), 
            static_context_s
            )
        
        # Pass output from variable selection through LSTM encoder and decoder
        encoder_output, state_h, state_c = self.define_lstm_encoder(
            past_encoder, 
            static_context_h, 
            static_context_c
            )
        
        decoder_output = self.define_lstm_decoder(
            future_decoder, 
            static_context_h, 
            static_context_c
            )

        # Gated skip connection before moving into the Temporal Fusion Decoder
        variable_selection_outputs = torch.cat([past_encoder, future_decoder], dim=0)
        lstm_outputs = torch.cat([encoder_output, decoder_output], dim=0)
        gated_outputs = self.gated_skip_connection(lstm_outputs)
        temporal_feature_outputs = self.add_norm(variable_selection_outputs.add(gated_outputs))
        temporal_feature_outputs = temporal_feature_outputs.transpose(0, 1)

        # Temporal Fusion Decoder

        # Static enrcihment layer
        static_enrichment_outputs = self.static_enrichment(
            temporal_feature_outputs, 
            static_context_e
            )

        # Temporal Self-attention layer
        mask = self.get_mask(static_enrichment_outputs)
        multihead_outputs, multihead_attention = self.multihead_attn(
            static_enrichment_outputs, 
            static_enrichment_outputs, 
            static_enrichment_outputs, 
            mask=mask
            )
        
        attention_gated_outputs = self.attention_gated_skip_connection(multihead_outputs)
        attention_outputs = self.attention_add_norm(
            attention_gated_outputs.add(static_enrichment_outputs)
            )

        # Position-wise feed-forward layer
        temporal_fusion_decoder_outputs = self.position_wise_feed_forward(attention_outputs)

        # Output layer
        gate_outputs = self.output_gated_skip_connection(temporal_fusion_decoder_outputs)
        norm_outputs = self.output_add_norm(gate_outputs.add(temporal_feature_outputs))

        output = self.output(norm_outputs[:, self.encoder_steps:, :]).view(-1,3)
        
        attention_weights = {
            'multihead_attention': multihead_attention,
            'static_weights': static_weights[Ellipsis, 0],
            'past_weights': past_weights[Ellipsis, 0, :],
            'future_weights': future_weights[Ellipsis, 0, :]
        }
        
        return  output, attention_weights

### testing
tft = TemporalFusionTransformer(params)
output, attention_weights = tft()


