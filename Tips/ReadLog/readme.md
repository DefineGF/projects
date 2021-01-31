##### 描述
从log文件中读取数据，并绘制
文件格式大致为：
```
[2021-01-30 16:01:06,093] - [trainer.py file line:64] - INFO: Current epoch learning rate: 1.000000e-04
[2021-01-30 16:05:48,191] - [trainer.py file line:84] - INFO: epoch: 1	 batch: 600
[2021-01-30 16:05:48,252] - [trainer.py file line:85] - INFO: rec_loss: 0.1074346155
[2021-01-30 16:05:48,273] - [trainer.py file line:95] - INFO: per_loss: 0.0365574583
[2021-01-30 16:05:48,278] - [trainer.py file line:102] - INFO: tpl_loss: 0.0022763107
[2021-01-30 16:05:48,402] - [trainer.py file line:107] - INFO: adv_loss: -0.0591784157
[2021-01-30 16:10:30,392] - [trainer.py file line:84] - INFO: epoch: 1	 batch: 1200
[2021-01-30 16:10:30,451] - [trainer.py file line:85] - INFO: rec_loss: 0.1209694073
[2021-01-30 16:10:30,472] - [trainer.py file line:95] - INFO: per_loss: 0.0425613485
[2021-01-30 16:10:30,477] - [trainer.py file line:102] - INFO: tpl_loss: 0.0029564472
[2021-01-30 16:10:30,601] - [trainer.py file line:107] - INFO: adv_loss: -0.0927379355
[2021-01-30 16:11:26,959] - [trainer.py file line:64] - INFO: Current epoch learning rate: 1.000000e-04
[2021-01-30 16:16:08,985] - [trainer.py file line:84] - INFO: epoch: 2	 batch: 600
[2021-01-30 16:16:09,044] - [trainer.py file line:85] - INFO: rec_loss: 0.0925423428
[2021-01-30 16:16:09,065] - [trainer.py file line:95] - INFO: per_loss: 0.0282687452
[2021-01-30 16:16:09,070] - [trainer.py file line:102] - INFO: tpl_loss: 0.0016764335
[2021-01-30 16:16:09,192] - [trainer.py file line:107] - INFO: adv_loss: -0.0571081638
[2021-01-30 16:20:50,736] - [trainer.py file line:84] - INFO: epoch: 2	 batch: 1200
[2021-01-30 16:20:50,795] - [trainer.py file line:85] - INFO: rec_loss: 0.0662220269
[2021-01-30 16:20:50,816] - [trainer.py file line:95] - INFO: per_loss: 0.0252009798
[2021-01-30 16:20:50,821] - [trainer.py file line:102] - INFO: tpl_loss: 0.0015876504
[2021-01-30 16:20:50,942] - [trainer.py file line:107] - INFO: adv_loss: -0.0348801091
```
##### 步骤
- 从文本中以 'Current' 问每轮的关键字，截取文本行段处理;
  - 从文本中获取 epoch，并将获取的四个 loss，分别放入 batch = 600 和 batch = 1200 的列表中；
- 对四个不同的loss 和 2 个 batch 分别绘图，最终为 2 * 4 样式的子图；
