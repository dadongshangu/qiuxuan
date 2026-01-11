# CDN仓库设置指南

## 📥 克隆CDN仓库

### 方法一：在现有目录中克隆（推荐）

1. **打开PowerShell或命令提示符**

2. **进入目标目录**：
   ```powershell
   cd E:\3.github\repositories\CDN
   ```

3. **克隆仓库到当前目录**：
   ```powershell
   git clone git@github.com:dadongshangu/CDN.git .
   ```
   注意：最后的 `.` 表示克隆到当前目录，而不是创建新的子目录

### 方法二：克隆到新目录

如果你想克隆到一个新的目录：

```powershell
cd E:\3.github\repositories
git clone git@github.com:dadongshangu/CDN.git CDN
```

这样会在 `E:\3.github\repositories\CDN` 目录下创建仓库。

## 📁 创建目录结构

克隆完成后，需要创建 `qiuxuan` 目录：

```powershell
cd E:\3.github\repositories\CDN
mkdir qiuxuan
```

## 📸 上传图片

1. **将图片文件复制到 `qiuxuan` 目录**：
   - `physics_question_13.png`
   - `physics_question_13_answer.png`
   - `physics_question_14.png`

2. **提交并推送**：
   ```powershell
   cd E:\3.github\repositories\CDN
   git add qiuxuan/*.png
   git commit -m "Add qiuxuan physics question images"
   git push origin master
   ```

## ✅ 验证

上传后，可以在浏览器中访问以下链接验证：

- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_13.png`
- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_13_answer.png`
- `https://cdn.jsdelivr.net/gh/dadongshangu/CDN@master/qiuxuan/physics_question_14.png`

如果能看到图片，说明设置成功！

## 🔧 如果遇到问题

### 问题1：SSH密钥未配置
如果提示权限错误，需要配置SSH密钥：
- 参考：https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### 问题2：仓库为空
如果仓库是空的，这是正常的。直接创建 `qiuxuan` 目录并上传图片即可。

### 问题3：目录已存在
如果 `qiuxuan` 目录已存在，直接放入图片文件即可。

---

**提示**：克隆完成后，告诉我，我可以帮你创建目录结构和准备上传命令。
