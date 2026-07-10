#!/bin/bash

# ================== 配置区 ==================
# 修改为你的实际路径
INPUT_DIR="/home/gwh/DPIO/blktrace/fio_results_nbcu_vs_numjobs"

# 检查目录是否存在
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ 错误：目录 $INPUT_DIR 不存在！"
    exit 1
fi

echo "🔍 正在处理目录: $INPUT_DIR"

# 计数器
renamed_count=0
skip_count=0

# 遍历所有 .json 文件
for file in "$INPUT_DIR"/*.json; do
    # 跳过不存在的文件（比如没有匹配的 json）
    [ -f "$file" ] || continue

    filename=$(basename "$file")
    
    # 使用正则匹配：时间戳前缀 + test_...
    if [[ $filename =~ ^[0-9]{8}_[0-9]{6}_(test_.+\.json)$ ]]; then
        new_name="${BASH_REMATCH[1]}"  # 提取捕获组：test_xxx.json
        new_path="$INPUT_DIR/$new_name"
        
        # 检查目标文件是否已存在，避免覆盖
        if [ -f "$new_path" ]; then
            echo "⚠️  已存在: $new_name （跳过）"
            ((skip_count++))
        else
            mv "$file" "$new_path"
            echo "✅ 重命名: $filename → $new_name"
            ((renamed_count++))
        fi
    else
        echo "⏭️  跳过: $filename （不匹配时间戳格式）"
        ((skip_count++))
    fi
done

echo "=================================="
echo "✅ 完成！共重命名 $renamed_count 个文件"
echo "⏭️  跳过 $skip_count 个文件"