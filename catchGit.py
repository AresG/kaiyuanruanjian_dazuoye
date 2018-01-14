# -*- coding:utf-8 -*-
'''
作者：Ecohnoch(熊楚原，岐山凤鸣)

包含功能：
    数据爬取
    数据输入mysql
    从mysql数据库中得到数据
    数据绘图

数据爬取：
    概述：从Github的Trend中爬取带有Ubuntu的所有的仓库的【用户名，仓库名，star数量，fork数量，用的什么编程语言，今天有多少人star，仓库URL】
    主要用到库：requests和pyquery

数据输入Mysql： 
    概述：先连接Mysql服务器，然后使用嵌入式Sql进行操作
    主要用到库：pymysql

从Mysql中得到数据：
    同上理

数据绘图：
    概述：使用Matplotlib结合了seaborn绘图
    主要用到库：pandas, seaborn, matplotlib

主要流程：
    先getHtml()获得目标网页源代码，然后getGithub()对网页进行解析，匹配得到n组7维数据
    然后inputToMysql()连接Mysql数据库，将n组7维数据保存入Mysql数据库
    然后outputFromMysql()将Mysql数据库中的数据导出，准备绘图
    最后dataVisible()绘图，绘制了3组数字数据的直方图、fork和star的散点图，使用编程语言的折线图
'''
import numpy
import pandas
import pymysql
import requests
import seaborn as sns 
import matplotlib.pyplot as plt  
from pyquery import PyQuery

# 获得网页源代码
def getHtml(url):
	return requests.get(url)

# 从源代码中查找匹配，若为空返回None
def match(matchObject, matchOrder, typ=str):
    if typ == str:
        tmp = matchObject.find(matchOrder).text()
        if tmp == '':
            return 'None'
        else:
            return tmp
    else:
    	return ''

# 从目标网页获取想要的七组数据，七组数据如下
# 输出格式：n行7元元组
def getGithub():
    '''
    return:
        userName: str
        repoName: str
        star: int
        fork: int
        language: str
        todayStar: int
        repoUrl: url
    '''
    ans = []
    r = getHtml("https://github.com/trending/Ubuntu")
    for i in PyQuery(r.content)(".repo-list>li"):
        repoUrl = "https://github.com"+ PyQuery(i).find(".mb-1 a").attr("href")
        name = match(PyQuery(i), ".mb-1 a").split('/')
        userName = name[0].strip()
        repoName = name[1].strip()
        starAndFork = match(PyQuery(i), "a.mr-3").replace(',', '').split(' ')
        star = int(starAndFork[0])
        fork = int(starAndFork[1])
        language = match(PyQuery(i).find("span"), "span")
        todayStar = int(PyQuery(i).find(".float-sm-right").text().split()[0].replace(',', ''))
        ans.append((userName, repoName, star, fork, language, todayStar, repoUrl))
    return ans

# 导入Mysql数据库
def inputToMysql():
    conn = pymysql.connect(host='127.0.0.1',port= 3306,user = 'root',passwd='123456',db='test')
    cur = conn.cursor()
    createTable = cur.execute('create table githubNormalInfo(userName varchar(100), repoName varchar(100), star numeric(5), fork numeric(5), language varchar(40), todayStar numeric(5), repoUrl varchar(200));')

    allData = getGithub()
    for i in allData:
        values = 'values(\''+i[0]+'\', \''+i[1]+'\', '+str(i[2])+', '+str(i[3])+', \''+i[4]+'\', '+str(i[5])+', \''+i[6]+'\');'
        cur.execute('insert into githubNormalInfo ' + values)
    conn.commit()
    cur.close()
    conn.close()

# 从Mysql数据库导出
def outputFromMysql():
    conn = pymysql.connect(host='127.0.0.1',port= 3306,user = 'root',passwd='123456',db='test')
    cur = conn.cursor()
    cur.execute("select * from githubNormalInfo")
    ans = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return ans

# 统计数据预处理
def datasVisiblePre():
    conn = pymysql.connect(host='127.0.0.1',port= 3306,user = 'root',passwd='123456',db='test')
    sql = "select * from githubNormalInfo"
    df = pandas.read_sql(sql, con=conn)
    conn.close()
    return df

# 统计数据绘图
def dataVisible():
    allData = datasVisiblePre()
    print(allData['todayStar'][0])
    f, axes = plt.subplots(2, 2, figsize=(7, 7), sharex=True)  
    # sns.set(palette="muted", color_codes=True)
    languageDict = {}
    lxx = []
    lyy = []
    for i in allData['language']:
    	if i not in languageDict.keys():
    		languageDict[i] = 1
    	else:
    		languageDict[i] = languageDict[i] + 1
    print(languageDict)
    for i in languageDict:
    	lxx.append(i)
    	lyy.append(languageDict[i])
    x = range(len(lxx))

    # Star 和 Fork的二维散点图
    sns.jointplot(x='star', y='fork', data=allData)
    # Star的直方图
    sns.distplot(allData['star'], kde=False, bins=20, ax=axes[0, 1])
    # Fork的直方图
    sns.distplot(allData['fork'], kde=False, bins=20, ax=axes[1, 0])
    # 今天Star个数的直方图
    sns.distplot(allData['todayStar'], kde=False, bins=2, ax=axes[0, 0])
    plt.show()

    # 各个仓库使用的编程语言统计
    plt.title('The number of each programming language')
    plt.plot(x, lyy, 'ro-')
    plt.xticks(x, lxx, rotation=45)
    plt.margins(0.08)
    plt.subplots_adjust(bottom=0.15)
    plt.show()

if __name__ == '__main__':
    dataVisible()