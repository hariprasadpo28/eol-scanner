FINAL_DATA=""
VERSION=$(python3 --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(python2.7 --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(python2 --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(python --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(go version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(php8 --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(php7 --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(php --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(node --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(nodejs --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(ruby --version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(java -version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(/usr/local/openresty/luajit/bin/luajit -v 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(tsc -v 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(scala -version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(ng version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION"#Separator#"
fi

VERSION=$(npm view react version 2>&1)
if [ "$VERSION" != "" ];then
    FINAL_DATA=$FINAL_DATA$VERSION
else
    VERSION="Notfound"
    FINAL_DATA=$FINAL_DATA$VERSION
fi
echo $FINAL_DATA
