default: dev

d:dev
dev:
	hugo serve --panicOnWarning

b:build
build:
	hugo build --panicOnWarning

.PHONY: default d dev b build

# generate zh-tw version
translate:
	bin/zh-tw.py

# 生成可交互键位图 keymap.html
keymap:
	python3 bin/keymap.py

# 探测屏幕布局（换显示器后跑，用于鼠标模式的屏幕跳转编号）
screens:
	swift bin/screens.swift

# 快捷键使用统计
keystat-install:
	bash bin/keystat/install.sh

keystat-report:
	python3 bin/keystat/report.py

.PHONY: keymap screens keystat-install keystat-report

epub:
	bin/epub

.PHONY: default doc translate
