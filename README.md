# pubmed 文献推送应用
2022-09-13

---
如果我想关注某个科研领域的最新成果，我会去 pubmed 通过关键词检索，然后查看最近发表的文献。
比如我比较关注 AAV 领域，那么设置一个关键词 "((aav) or (raav)) not (anca)" 就会检索到相关的文献列表，设置一下排序方式，按照最新发表的时间排序，就可以查看自己感兴趣的文献了。
但是每天新发的文献很少或者根本没有，所以要攒一攒文献量再定期去查，就想做一个自动定期推送文献的脚本，每周/月把相关的新文献列表发送到手机/邮件里。

## 程序的主题思路
首先做一个 pubmed 的爬虫，把每周新发表的文献相关信息列表爬出来。
pubmed 爬到的信息包括：发表时间、杂志、作者、摘要、文献类型等等，把这些信息做成 excel 文件。
再写一个自动邮件发送的脚本，发送到个人邮箱里。代码见<https://github.com/datugou/PubMed_papers/blob/main/send_email_pubmed_papers.py>。
最后设置一个 GitHub Action 每周定时执行一下上面的脚本。代码见<>。

一个简单的文献推送应用就做好了！

## 补充
### 给文献标出杂志的影响因子
可是每周很多文献我不想全去看，只想要看好的文献，把灌水的过滤掉。pubmed 的信息只有杂志名称，需要再写一个通过杂志名查影响因子的爬虫。
在网上随便找了俩个查影响因子的网站 <https://www.medsci.cn/> 和 <https://www.letpub.com.cn/>，可以查到 IF、CS、cts（不知道这三个分的区别是啥，都爬下来了）和 JCR 分区。

最后就得到了这样的文献列表：
![image](https://user-images.githubusercontent.com/30107520/189705623-4980c27e-3522-4046-8b8a-764fe009ee95.png)

### 设置邮箱信息的 secrets 值，避免暴露个人隐私信息
在 Settings → Secrets → Dependabot → New repository secret 设置邮箱服务器信息。
需要填写以下内容，163 邮箱信息获取教程。
![image](https://user-images.githubusercontent.com/30107520/189717557-3d7fda02-5aea-4788-a1f0-e8fc6bc49e32.png)
