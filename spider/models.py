from django.db import models

# Create your models here.

# CREATE TABLE `spider` (
#   `id`INT not null auto_increment,
#   `name` varchar(50) NOT NULL,
#   `phone` varchar(100) DEFAULT NULL,
#   `corporate_name` varchar(50) NOT NULL,
#   `city` varchar(50) NOT NULL,
#   `region` varchar(50) NOT NULL,
#   `address` varchar(100) NOT NULL,
#   `url` varchar(250) NOT NULL,
#   `year` int(4) NOT NULL,
#   `personnel_scale` varchar(50) not null,
#   `industry` varchar(50) NOT NULL,
#   `keyword` varchar(50) not null,
#   `datetime` date NOT NULL,
#   `source` varchar(25) DEFAULT NULL,
#   `insertdate` date NOT null,
#   PRIMARY KEY (id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8;


class Spider(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField('姓名',max_length=50,null=True)
    history_name=models.CharField('公司历史名称',max_length=50,null=True)
    phone=models.CharField('电话',max_length=100)
    email=models.CharField('邮箱',max_length=50)
    corporate_name=models.CharField('公司名称',max_length=50,null=False)
    city=models.CharField('省份',max_length=50,null=False)
    region=models.CharField('地市',max_length=50,null=False)
    address=models.CharField('地址',max_length=100,null=False)
    url=models.CharField(max_length=250,null=False,unique=True)
    year=models.IntegerField('存入年份',max_length=4,null=False)
    personnel_scale=models.CharField('人员规模',max_length=50,null=False)
    industry=models.CharField('行业分类',max_length=50,null=False)
    keyword=models.CharField('关键字',max_length=50,null=False)
    datetime=models.DateField('发布日期',null=False)
    source=models.CharField('来源',max_length=25,null=False)
    insertdate=models.DateField('插入时间',auto_now_add=True)
    source_corporate_name=models.CharField(max_length=250)

    class Meta:
        db_table="spider"
