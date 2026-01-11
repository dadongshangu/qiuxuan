# 图片文件目录

本目录用于存放学习总结中使用的图片文件。

## 📸 当前需要的图片文件

根据文档引用，以下图片文件需要上传：

1. **physics_question_13.png** - 物理第13题图
2. **physics_question_13_answer.png** - 物理第13题答案图
3. **physics_question_14.png** - 物理第14题图

## 📤 如何上传图片

**重要**：图片需要上传到CDN仓库，而不是当前仓库！

1. 克隆或访问CDN仓库：`git@github.com:dadongshangu/CDN.git`
2. 在CDN仓库中创建 `qiuxuan/` 目录（如果不存在）
3. 将图片文件复制到CDN仓库的 `qiuxuan/` 目录
4. 确保文件名与文档中引用的名称一致
5. 在CDN仓库中提交：
   ```bash
   cd CDN
   git add qiuxuan/*.png
   git commit -m "Add qiuxuan physics question images"
   git push origin master
   ```

详细说明请参考：[图片上传说明](../../docs/图片上传说明.md)

## 🔗 CDN链接

图片上传后，会自动通过 jsDelivr CDN 加速访问（使用专门的CDN仓库）：

- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_13.png`
- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_13_answer.png`
- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_14.png`

**注意**：图片需要上传到CDN仓库（`git@github.com:dadongshangu/CDN.git`）的 `qiuxuan/` 目录，而不是当前仓库。

## 📝 更多说明

详细的上传说明请参考：[图片上传说明](../../docs/图片上传说明.md)
