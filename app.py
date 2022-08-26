from appl_domain.__init__ import create_app

if __name__ == '__main__':
    application = create_app()
    application.app_context().push()

