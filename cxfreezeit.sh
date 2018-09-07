#!/bin/bash

cxfreeze knasboll.py --target-dir knasboll_win64
cp generic_xml.xml knasboll_win64
cd knasboll_win64
/c/Program/7-Zip/7z.exe a knasboll *
mv knasboll.7z ..
cd ..
rm -Rf knasboll_win64
echo 'Done!'
