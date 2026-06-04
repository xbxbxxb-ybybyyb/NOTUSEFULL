import os
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly import tools
import plotly
from artifacts.plot_data_mongo import PlotData
from artifacts.save_to_mongo import MongoDB
from dateutil.relativedelta import relativedelta
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
pyplt = plotly.offline.plot


class EvalPlot:
    def __init__(self, user_id, label_name, html_path):
        self.label_name = label_name
        self.user_id = user_id
        self.html_path = html_path
        self.pltd = PlotData(user_id, label_name)
        self.db = MongoDB()
        self.fp = FactorProvider(self.user_id)
        self.stock_list = None
        self.factor_name_list = None

    def __set_stocks(self):
        if not self.stock_list:
            self.stock_list = self.pltd.get_stock_list()

    def __set_factors(self):
        if not self.factor_name_list:
            self.factor_name_list = list(self.fp.load_info_from_dfs("factor", source_type="public"))

    def plot_K_IC(self, freq="3s"):
        self.__set_stocks()
        self.__set_factors()
        for stock in self.stock_list:
            for factor in self.factor_name_list:
                self.__plot_K_IC(stock, factor, freq=freq)

    def __plot_K_IC(self, stock, factor, freq="3s"):
        """画图， 每日IC & rankIC"""
        print(f"开始绘制stock:{stock}, factor:{factor}的IC & rankIC图。")
        data = self.pltd.get_ic_rankic_data(freq, factor, stock)
        data["IC"] = data["normal_ic"]
        data["RankIC"] = data["rank_ic"]

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_width=[0.2, 0.7],
                            subplot_titles=["Daily K & IC & RankIC", ""],
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
                            )

        # 绘制k数据
        fig.add_trace(go.Candlestick(x=data["date"], open=data["open"], high=data["high"],
                                     low=data["low"], close=data["close"], name="K_line", showlegend=True),
                      row=1, col=1, secondary_y=False
                      )

        # 绘制IC
        fig.add_trace(go.Scatter(x=data["date"], y=data["IC"], name="IC", showlegend=True,
                                 fill="tozeroy", fillcolor="rgba(250,179,135,0.4)", line_color="rgba(255,255,255,0)"),
                      row=1, col=1, secondary_y=True
                      )

        # 绘制RankIC
        fig.add_trace(go.Scatter(x=data["date"], y=data["RankIC"], name="RankIC", showlegend=True,
                                 fill="tozeroy", fillcolor="rgba(135,206,250,0.4)", line_color="rgba(255,255,255,0)"),
                      row=1, col=1, secondary_y=True
                      )

        # 绘制成交量数据
        fig.add_trace(go.Bar(x=data['date'], y=data['amt'], showlegend=True, name="TotalValueTrade",
                             marker={"color": "rgba(240,0,0,0.3)"}),
                      row=2, col=1)

        # Do not show OHLC's rangeslider plot
        fig.update(layout_xaxis_rangeslider_visible=False)
        fig.update_xaxes(tickvals=[data["date"][0], data["date"][round(len(data) / 4)],
                                   data["date"][round(2 * len(data) / 4)], data["date"][round(3 * len(data) / 4)],
                                   data["date"][len(data) - 1]])
        fig.update_layout(width=800, height=500,
                          legend=dict(orientation="h", yanchor="top"))
        file_name = f"IC_RankIC_K_{self.label_name}_{factor}_{stock}.html"
        file_path = os.path.abspath(self.html_path)
        save_path = os.path.join(file_path, file_name)
        with open(save_path, "w") as f:
            f.write(fig.to_html(full_html=False, ))
        res = self.db.UploadFile(file_name, save_path)
        date = "{}_{}".format(self.pltd.start_date, self.pltd.end_date)
        self.db.plot_uniquekey_todb(stock=stock, factor=factor, label_name=self.label_name, date=date, freq=freq,
                                      uniquekey=res.text, source='ic')
        return fig



if __name__ == '__main__':
    ep = EvalPlot(user_id="016869", label_name="LabelFirstPeak_th10_120s", html_path="./")

    # # 每日IC & rankIC
    # # 688012.SH "ask_9_price_diff_20"
    ep.plot_K_IC()



