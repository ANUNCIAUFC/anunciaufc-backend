from flask_mail import Mail, Message

class MailService:
    def __init__(self,app):
        self.mail = Mail(app)

    def sendmail(self , email , confirmation_code):
        try:
            msg = Message('Confirmação de Cadastro', recipients=[email])
            msg.body = f"Seu código de verificação é: {confirmation_code}"
            self.mail.send(msg)
        except Exception as e:
            raise Exception(f"Error ao enviar o e-mail : str({e})")
        
    def send_accept_mail(self, email):
        try:
            msg = Message('Anúncio validado!', recipients=[email])
            msg.body = f"Seu anúncio cadastrado no AnunciaUFC foi validado pela equipe."
            self.mail.send(msg)
        except Exception as e:
            raise Exception(f"Error ao enviar o e-mail : str({e})")
        
    def send_refused_mail(self, email):
        try:
            msg = Message('Anúncio rejeitado!', recipients=[email])
            msg.body = f"Seu anúncio cadastrado no AnunciaUFC foi rejeitado pela equipe.\nSeu anúncio violou as normas de segurança do site."
            self.mail.send(msg)
        except Exception as e:
            raise Exception(f"Error ao enviar o e-mail : str({e})")