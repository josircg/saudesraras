import poplib
import environ


env = environ.Env()
env_filename = "../eucs_platform/settings/local.env"
environ.Env.read_env(env_filename)
password = env('EMAIL_HOST_PASSWORD')
username = 'civis@apps.ibict.br'


def test_poplib():
    Mailbox = poplib.POP3('pop.apps.ibict.br', port=110)
    Mailbox.user(username)
    Mailbox.pass_(password)
    print('Connected')
    numMessages = len(Mailbox.list()[1])
    for i in range(numMessages):
        for msg in Mailbox.retr(i+1)[1]:
            print(msg)
    Mailbox.quit()


test_poplib()
