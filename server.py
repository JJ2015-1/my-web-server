"""
设计服务器架构
创建套接字：监听指定端口
接受连接：等待客户端连接
解析请求：读取并解析HTTP请求
处理请求：根据请求路径查找文件
生成响应：返回文件内容或错误信息
关闭连接：完成响应后关闭连接

处理流程
启动服务器 → 绑定端口 → 监听连接 → 接受请求 →
解析HTTP请求 → 验证请求 → 查找文件 →
生成响应 → 发送响应 → 关闭连接
"""
import socket #HTTP协议基于TCP，而socket是TCP/IP的编程接口。
import os #用于文件操作
import threading #多线程编程，用于并发处理多个用户请求
from mimetypes import guess_type #根据文件扩展名猜测其MIME类型

class SimpleWebServer:
    def __init__(self,host='0.0.0.0',port=9000,root_dir='.'):
        """
        :param host: 服务器监听的主机地址，默认‘0.0.0.0’监听所有可用接口
        :param port: 服务器监听的端口号，默认使用8080
        :param root_dir:服务器根目录，默认当前目录，是web服务器用于存放所有可访问文件的基准目录
        """
        #初始化实例变量
        self.host=host
        self.port=port
        self.root_dir=os.path.abspath(root_dir)#将根目录转换为绝对路径
        #创建服务器套接字,TCP套接字对象
        self.server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)#使用IPV4和TCP协议
        #设置套接字选项
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) #允许服务器快速重启时重复使用相同的地址和端口

    def start(self):
        """启动服务器"""
        #套接字绑定与监听
        self.server_socket.bind((self.host,self.port))#绑定到指定的(host,port)元祖
        self.server_socket.listen(5)#启用服务器接收连接，等待队列数字超过5的新链接会被拒绝
        #服务状态输出，明确告诉服务员监听地址和文件服务根目录
        print(f'Server started on http://{self.host}:{self.port}')
        print(f'Serving files from:{self.root_dir}')

        #主服务循环
        try:
            while True:
                client_socket,client_address=self.server_socket.accept()#返回客户端(IP,port)
                print(f'Connection from:{client_address}')

                #多线程处理
                thread=threading.Thread(
                    target=self.handle_client, #指定线程要执行的函数
                    args=(client_socket,) #传递给处理函数的参数，‘，’表示元祖
                )
                thread.start()#立即启动线程
            #关闭处理
        except KeyboardInterrupt:#捕捉ctrl+c信号，安全关闭服务器
            print('\nServer is shutting down...')
            self.server_socket.close()

    def handle_client(self, client_socket):
        """处理客户端请求"""
        try:
            request_data = client_socket.recv(1024).decode('utf-8')
            if not request_data:
                return

            request_line = request_data.split('\r\n')[0]
            parts = request_line.split()

            # 基本验证
            if len(parts) < 2:
                response = self.create_response(400, "Bad Request")
                client_socket.sendall(response)
                return

            method, path = parts[0], parts[1]

            # 只支持 GET 方法
            if method != 'GET':
                response = self.create_response(405, "Method Not Allowed")  # 修正方法名
                client_socket.sendall(response)
                return

            # 默认页面重定向
            if path == '/':
                path = '/index.html'

            # 构造安全路径
            file_path = os.path.join(self.root_dir, path.lstrip('/'))
            if not os.path.abspath(file_path).startswith(self.root_dir):
                response = self.create_response(403, "Forbidden")
                client_socket.sendall(response)
                return

            # 检查文件是否存在
            if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                with open(file_path, 'rb') as file:
                    content = file.read()
                mime_type, _ = guess_type(file_path)
                mime_type = mime_type or 'text/plain'
                response = self.create_response(200, "OK", content, mime_type)
            else:
                response = self.create_response(404, "Not Found", b"<h1>404 Not Found</h1>")

            # 关键修复：确保响应被发送
            client_socket.sendall(response)  # 所有成功/失败分支都要发送响应

        except Exception as e:
            print(f"Error handling request: {e}")
            response = self.create_response(500, "Internal Server Error", b"<h1>500 Internal Server Error</h1>")
            client_socket.sendall(response)  # 异常时也发送响应
        finally:
            client_socket.close()

    def create_response(self,status_code,status_message,content=b'',content_type='text/html'):
        """

        :param status_code: HTTP状态码
        :param status_message: 状态描述
        :param content: 响应正文，默认为空
        :param content_type: MIME类型，默认
        """
        #响应行构造
        response_line=f'HTTP/1.1 {status_code} {status_message}\r\n'
        #响应头配置
        headers={#默认
            "Server":"SimplePythonWebServer",#服务器标识（自定义）
            "Connection":"close",#关闭短连接
        }
        if content:#当有内容添加时
            headers["Content-Length"]=str(len(content))
            headers["Content-Type"]=content_type
        #头部格式化
        headers_str="\r\n".join(f"{k}: {v}" for k,v in headers.items())+"\r\n\r\n"
        #字节流组装
        response=(
            response_line.encode('utf-8')+#响应行
            headers_str.encode('utf-8')#头部
        )
        if content:
            response+=content if isinstance(content,bytes)else content.encode('utf-8')
        return response

if __name__ == '__main__':
    # 使用当前目录作为根目录
    server = SimpleWebServer(port=9000, root_dir=r'E:\PythonProject3\web服务器\my_web_root')
    server.start()
