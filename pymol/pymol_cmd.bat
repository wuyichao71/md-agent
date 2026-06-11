@echo off
curl -s -X POST http://localhost:9123/RPC2 ^
  -H "Content-Type: text/xml" ^
  -d "<?xml version=\"1.0\"?><methodCall><methodName>do</methodName><params><param><value><string>%*</string></value></param></params></methodCall>"