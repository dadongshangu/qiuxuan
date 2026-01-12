# CDN仓库设置指南

## 📥 克隆CDN仓库

### 方法一：使用稀疏检出（推荐）⭐

**适用场景**：CDN仓库文件较多，完整克隆时网络不稳定或速度慢

**优势**：
- ✅ 只下载 `qiuxuan/` 目录，大幅减少下载量
- ✅ 避免网络超时问题
- ✅ 后续操作（add、commit、push）不受影响

#### 自动配置（推荐）

1. **运行配置脚本**：
   ```powershell
   cd E:\3.github\repositories\qiuxuan
   .\scripts\setup_cdn_sparse_checkout.ps1
   ```

   脚本会自动：
   - 初始化或配置Git仓库
   - 启用稀疏检出
   - 配置只检出 `qiuxuan/` 目录
   - 拉取需要的文件

#### 手动配置

如果脚本无法运行，可以手动执行以下步骤：

1. **进入CDN仓库目录**：
   ```powershell
   cd E:\3.github\repositories\CDN
   ```

2. **初始化Git仓库（如果还没有）**：
   ```powershell
   git init
   git remote add origin git@github.com:dadongshangu/CDN.git
   ```

3. **启用稀疏检出**：
   ```powershell
   git config core.sparseCheckout true
   ```

4. **配置只检出qiuxuan目录**：
   ```powershell
   echo "qiuxuan/*" > .git/info/sparse-checkout
   ```

5. **拉取（只下载qiuxuan目录）**：
   ```powershell
   git pull origin master --allow-unrelated-histories
   ```

   如果仓库中还没有 `qiuxuan` 目录，这个命令可能会失败，但这是正常的。你可以直接创建目录并上传图片。

### 方法二：完整克隆（不推荐，网络慢时容易失败）

#### 在现有目录中克隆

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

#### 克隆到新目录

如果你想克隆到一个新的目录：

```powershell
cd E:\3.github\repositories
git clone git@github.com:dadongshangu/CDN.git CDN
```

这样会在 `E:\3.github\repositories\CDN` 目录下创建仓库。

**注意**：如果CDN仓库文件较多（如601个对象），完整克隆可能因为网络问题失败。建议使用**方法一（稀疏检出）**。

## 📁 创建目录结构

如果使用稀疏检出，`qiuxuan` 目录可能已经存在（如果远程仓库中有）。如果不存在，需要创建：

```powershell
cd E:\3.github\repositories\CDN
mkdir qiuxuan
```

**注意**：即使远程仓库中还没有 `qiuxuan` 目录，你也可以直接创建并上传图片。Git会正确处理新目录。

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

### 问题1：网络连接失败（fetch-pack: unexpected disconnect）

**症状**：
```
fetch-pack: unexpected disconnect while reading sideband packetts: 0% (1/601)
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

**原因**：CDN仓库文件较多，完整克隆时网络不稳定

**解决方案**：使用**稀疏检出（方法一）**，只下载 `qiuxuan/` 目录

### 问题2：SSH密钥未配置
如果提示权限错误，需要配置SSH密钥：
- 参考：https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### 问题3：仓库为空或qiuxuan目录不存在
如果仓库是空的或没有 `qiuxuan` 目录，这是正常的。直接创建 `qiuxuan` 目录并上传图片即可：

```powershell
cd E:\3.github\repositories\CDN
mkdir qiuxuan
# 复制图片到 qiuxuan/ 目录
git add qiuxuan/*.png
git commit -m "Add qiuxuan images"
git push origin master
```

### 问题4：目录已存在
如果 `qiuxuan` 目录已存在，直接放入图片文件即可。

### 问题5：稀疏检出配置后仍然下载全部文件

检查稀疏检出配置：
```powershell
# 查看配置
Get-Content .git/info/sparse-checkout

# 应该显示：qiuxuan/*
# 如果不是，重新配置：
echo "qiuxuan/*" > .git/info/sparse-checkout
git read-tree -mu HEAD
```

---

**提示**：如果遇到其他问题，可以运行配置脚本 `.\scripts\setup_cdn_sparse_checkout.ps1` 来自动配置。
