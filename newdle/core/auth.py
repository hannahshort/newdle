from flask import current_app, render_template
from flask_multipass import Multipass
from itsdangerous import URLSafeTimedSerializer
from werkzeug.local import LocalProxy


class NewdleMultipass(Multipass):
    def handle_auth_error(self, exc, redirect_to_login=False):
        payload = {'error': str(exc), 'token': None}
        return render_template('login_result.html', payload=payload)


multipass = NewdleMultipass()

secure_serializer = LocalProxy(
    lambda: URLSafeTimedSerializer(current_app.config['SECRET_KEY'], b'newdle')
)


@multipass.identity_handler
def process_identity(identity_info):
    assert not any(x is None for x in identity_info.data.values())
    token = app_token_from_multipass(identity_info)
    payload = {'error': None, 'token': token}
    return render_template('login_result.html', payload=payload)


def app_token_from_multipass(identity_info):
    return secure_serializer.dumps(
        {
            'email': identity_info.data['email'],
            'first_name': identity_info.data['given_name'],
            'last_name': identity_info.data['family_name'],
            'uid': identity_info.identifier,
        },
        salt='app-token',
    )


def app_token_from_dummy():
    return secure_serializer.dumps(
        {
            'email': 'example@example.com',
            'first_name': 'Guinea',
            'last_name': 'Pig',
            'uid': '-',
        },
        salt='app-token',
    )


def user_info_from_app_token(app_token):
    return secure_serializer.loads(
        app_token, salt='app-token', max_age=current_app.config['TOKEN_LIFETIME']
    )


def search_users(name, email, limit):
    criteria = {}
    if name:
        criteria['name'] = name
    if email:
        criteria['email'] = email

    identities, total = multipass.search_identities_ex(
        {'newdle-search'}, limit=limit, criteria=criteria
    )
    users = [
        {
            'email': identity.data['email'],
            'first_name': identity.data['given_name'],
            'last_name': identity.data['family_name'],
            'uid': identity.identifier,
        }
        for identity in sorted(identities, key=lambda x: x.data['name'])
    ]
    return total, users
