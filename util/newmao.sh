#!/bin/zsh

git clone https://github.com/damaxwell/mao.git mao-src
ln -s mao-src/mao mao

cd mao-src
head_sha=$(git rev-parse --short head)
cd ..

cat <<EOF > checkout-mao.sh
#!/bin/sh
git clone https://github.com/damaxwell/mao.git mao-src
cd mao-src
git checkout $head_sha
cd ..
ln -s mao-src/mao mao
EOF
