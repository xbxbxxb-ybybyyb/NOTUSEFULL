from email.mime.text import MIMEText
import smtplib

if True:
    txt = '1111'
    msg = MIMEText(txt, 'plain', 'utf-8')
    from_addr = '''XquantIDE@htsc.com'''
    password = '''Admin@123'''
    smtp_server = '168.8.250.75'
    server = smtplib.SMTP()
    server.connect(smtp_server, 25)  # SMTP协议默认端口是25
    server.set_debuglevel(1)
    server.login('XquantIDE', password)
    server.sendmail(from_addr, ['shenjunling@htsc.com'], msg.as_string())
    server.quit()

