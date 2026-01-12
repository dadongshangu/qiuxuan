# CDN仓库稀疏检出配置脚本
# 此脚本用于配置Git稀疏检出，只下载qiuxuan目录，避免同步整个仓库

param(
    [string]$CdnRepoPath = "E:\3.github\repositories\CDN",
    [string]$RemoteUrl = "git@github.com:dadongshangu/CDN.git",
    [string]$Branch = "master"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CDN仓库稀疏检出配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查目录是否存在
if (-not (Test-Path $CdnRepoPath)) {
    Write-Host "创建目录: $CdnRepoPath" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $CdnRepoPath -Force | Out-Null
}

# 进入CDN仓库目录
Set-Location $CdnRepoPath
Write-Host "当前目录: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# 检查是否已经是Git仓库
$isGitRepo = Test-Path ".git"

if (-not $isGitRepo) {
    Write-Host "初始化Git仓库..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: Git初始化失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Git仓库初始化成功" -ForegroundColor Green
} else {
    Write-Host "✓ 已存在Git仓库" -ForegroundColor Green
}

# 检查远程仓库配置
Write-Host ""
Write-Host "检查远程仓库配置..." -ForegroundColor Yellow
$remoteExists = git remote | Select-String -Pattern "origin"

if (-not $remoteExists) {
    Write-Host "添加远程仓库: $RemoteUrl" -ForegroundColor Yellow
    git remote add origin $RemoteUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: 添加远程仓库失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 远程仓库添加成功" -ForegroundColor Green
} else {
    $currentRemote = git remote get-url origin
    Write-Host "✓ 远程仓库已存在: $currentRemote" -ForegroundColor Green
    
    # 如果URL不匹配，询问是否更新
    if ($currentRemote -ne $RemoteUrl) {
        Write-Host "警告: 远程仓库URL不匹配" -ForegroundColor Yellow
        Write-Host "  当前: $currentRemote" -ForegroundColor Yellow
        Write-Host "  期望: $RemoteUrl" -ForegroundColor Yellow
        $update = Read-Host "是否更新远程仓库URL? (y/n)"
        if ($update -eq "y" -or $update -eq "Y") {
            git remote set-url origin $RemoteUrl
            Write-Host "✓ 远程仓库URL已更新" -ForegroundColor Green
        }
    }
}

# 启用稀疏检出
Write-Host ""
Write-Host "配置稀疏检出..." -ForegroundColor Yellow
git config core.sparseCheckout true
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 启用稀疏检出失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 稀疏检出已启用" -ForegroundColor Green

# 创建.git/info目录（如果不存在）
$infoDir = ".git\info"
if (-not (Test-Path $infoDir)) {
    New-Item -ItemType Directory -Path $infoDir -Force | Out-Null
}

# 配置只检出qiuxuan目录
Write-Host "配置只检出qiuxuan目录..." -ForegroundColor Yellow
"qiuxuan/*" | Out-File -FilePath ".git\info\sparse-checkout" -Encoding utf8 -NoNewline
Write-Host "✓ 稀疏检出配置已设置" -ForegroundColor Green

# 显示配置内容
Write-Host ""
Write-Host "稀疏检出配置内容:" -ForegroundColor Cyan
Get-Content ".git\info\sparse-checkout" | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

# 尝试拉取
Write-Host ""
Write-Host "开始拉取qiuxuan目录（只下载需要的文件）..." -ForegroundColor Yellow
Write-Host "注意: 这只会下载qiuxuan目录，不会下载整个仓库" -ForegroundColor Cyan
Write-Host ""

# 检查是否有本地提交
$hasLocalCommits = git log --oneline 2>$null | Select-Object -First 1

if ($hasLocalCommits) {
    Write-Host "检测到本地提交，使用 --allow-unrelated-histories" -ForegroundColor Yellow
    git pull origin $Branch --allow-unrelated-histories
} else {
    Write-Host "首次拉取，使用 fetch + checkout" -ForegroundColor Yellow
    git fetch origin $Branch
    if ($LASTEXITCODE -eq 0) {
        git checkout -b $Branch origin/$Branch 2>$null
        if ($LASTEXITCODE -ne 0) {
            # 如果分支已存在，直接checkout
            git checkout $Branch 2>$null
        }
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 稀疏检出配置成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # 验证qiuxuan目录
    if (Test-Path "qiuxuan") {
        $fileCount = (Get-ChildItem -Path "qiuxuan" -File -ErrorAction SilentlyContinue).Count
        Write-Host "✓ qiuxuan目录已存在" -ForegroundColor Green
        Write-Host "  文件数量: $fileCount" -ForegroundColor Gray
    } else {
        Write-Host "ℹ qiuxuan目录不存在（这是正常的，如果仓库中还没有这个目录）" -ForegroundColor Yellow
        Write-Host "  你可以直接创建目录并上传图片" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "后续操作:" -ForegroundColor Cyan
    Write-Host "1. 将图片文件复制到 qiuxuan/ 目录" -ForegroundColor White
    Write-Host "2. 使用以下命令提交:" -ForegroundColor White
    Write-Host "   git add qiuxuan/*.png" -ForegroundColor Gray
    Write-Host "   git commit -m 'Add qiuxuan images'" -ForegroundColor Gray
    Write-Host "   git push origin $Branch" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 拉取失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 网络连接问题（中国网络访问GitHub可能较慢）" -ForegroundColor White
    Write-Host "2. 远程仓库中还没有qiuxuan目录" -ForegroundColor White
    Write-Host "3. SSH密钥未配置" -ForegroundColor White
    Write-Host ""
    Write-Host "解决方案:" -ForegroundColor Yellow
    Write-Host "1. 如果仓库中还没有qiuxuan目录，可以直接创建:" -ForegroundColor White
    Write-Host "   mkdir qiuxuan" -ForegroundColor Gray
    Write-Host "   # 然后添加图片文件" -ForegroundColor Gray
    Write-Host "   git add qiuxuan/*.png" -ForegroundColor Gray
    Write-Host "   git commit -m 'Add qiuxuan images'" -ForegroundColor Gray
    Write-Host "   git push origin $Branch" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. 检查网络连接和SSH配置" -ForegroundColor White
    Write-Host ""
}
