请写一个caddy的json配置
要求如下

1. http://localhost/potree 托管 /srv/www/potree 目录
2. http://localhost/image 代理到 http://localhost:9000
3. http://localhost/api 代理到 http://localhost:8000，同时添加CORS头
4. http://localhost/ 托管 /srv/www/earth 目录
