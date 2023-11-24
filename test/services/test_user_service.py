import pytest
from http import HTTPStatus
from api.domain.models import User
from api.domain.services import UserService
from api.domain.errors import DomainError, NoContentError, NotFoundError
from test.conftest import user_service



@pytest.fixture(scope='function')
def valid_user():
    return User(**{
        'id': 1, 
        'email': 'teste@email.com', 
        'password': '1aA!', 
        'admin': False
    })


# Find All Users Tests
def test_find_all_users_no_content(user_service: UserService):
    user_service.user_repository.find_all.return_value = []

    with pytest.raises(NoContentError) as exception:
        user_service.find_all()
    
    assert exception.value.status_code == HTTPStatus.NO_CONTENT


def test_find_all_users_success(valid_user: User, user_service: UserService):
    user_service.user_repository.find_all.return_value = [valid_user]

    users = user_service.find_all()
    
    assert len(users) > 0
    assert isinstance(users[0], User)


# Find User By Id Tests
def test_find_by_id_user_not_found(user_service: UserService):
    user_service.user_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundError) as exception:
        user_service.find_by_id(1)
    
    assert exception.value.message == 'Usuário não encontrado.'
    assert exception.value.status_code == HTTPStatus.NOT_FOUND


def test_find_by_id_user_success(valid_user: User, user_service: UserService):
    user_service.user_repository.find_by_id.return_value = valid_user

    user = user_service.find_by_id(1)
    
    assert user is not None
    assert isinstance(user, User)
    assert user.id == valid_user.id


# Create User Tests
def test_create_user_password_less_then_4_chars(valid_user: User, user_service: UserService):
    valid_user.password = 'aa'

    with pytest.raises(ValueError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.args[0] == 'Sua senha deve conter pelo menos 4 caracteres.'


def test_create_user_password_with_no_digits(valid_user: User, user_service: UserService):
    valid_user.password = 'aaaa'

    with pytest.raises(ValueError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.args[0] == 'Sua senha deve conter numeros.'


def test_create_user_password_with_no_lowercase(valid_user: User, user_service: UserService):
    valid_user.password = '1AAA'

    with pytest.raises(ValueError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.args[0] == 'Sua senha deve conter letras minúsculas.'


def test_create_user_password_with_no_uppercase(valid_user: User, user_service: UserService):
    valid_user.password = '1aaa'

    with pytest.raises(ValueError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.args[0] == 'Sua senha deve conter letras maiúsculas.'


def test_create_user_password_with_no_special(valid_user: User, user_service: UserService):
    valid_user.password = '1Aaa'

    with pytest.raises(ValueError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.args[0] == 'Sua senha deve conter caracteres especiais.'


def test_create_user_email_registered(valid_user: User, user_service: UserService):
    user_service.user_repository.find_by_email.return_value = valid_user.email

    with pytest.raises(DomainError) as exception:
        user_service.create(valid_user)
    
    assert exception.value.message == 'Email já cadastrado.'
    assert exception.value.status_code == HTTPStatus.BAD_REQUEST


def test_create_user_success(valid_user: User, user_service: UserService):
    user_service.user_repository.find_by_email.return_value = None
    user_service.user_repository.insert.return_value = valid_user

    user = user_service.create(valid_user)
    
    assert user is not None
    assert isinstance(user, User)
    assert user.id is not None


# Update User Tests
def test_update_user_incorect_password(valid_user: User, user_service: UserService):
    user_in_db = valid_user.copy()
    user_in_db.password = user_service.crypt_service.hash('senha_incorreta')
    user_service.user_repository.find_by_id.return_value = user_in_db

    with pytest.raises(DomainError) as exception:
        user_service.update(valid_user)
    
    assert exception.value.message == 'Senha incorreta.'
    assert exception.value.status_code == HTTPStatus.BAD_REQUEST


def test_update_user_email_registered(valid_user: User, user_service: UserService):
    user_in_db = valid_user.copy()
    user_in_db.password = user_service.crypt_service.hash(valid_user.password)
    other_user = valid_user.copy()
    other_user.id = 123
    user_service.user_repository.find_by_id.return_value = user_in_db
    user_service.user_repository.find_by_email.return_value = other_user

    with pytest.raises(DomainError) as exception:
        user_service.update(valid_user)
    
    assert exception.value.message == 'Email já cadastrado.'
    assert exception.value.status_code == HTTPStatus.BAD_REQUEST


def test_update_user_success(valid_user: User, user_service: UserService):
    updated_user = valid_user.copy()
    updated_user.email = 'updatedemail@gmail.com'
    valid_user.password = user_service.crypt_service.hash(valid_user.password)
    user_service.user_repository.find_by_id.return_value = valid_user
    user_service.user_repository.find_by_email.return_value = valid_user
    user_service.user_repository.update.return_value = updated_user

    user = user_service.update(updated_user)
    
    assert user is not None
    assert isinstance(user, User)
    assert updated_user.email != valid_user.email


# Change Password Test
def test_change_password_incorrect_password(valid_user: User, user_service: UserService):
    valid_user.password = user_service.crypt_service.hash(valid_user.password)
    user_service.user_repository.find_by_id.return_value = valid_user

    with pytest.raises(DomainError) as exception:
        user_service.change_password(1, '1234', '5323')
    
    assert exception.value.message == 'Senha incorreta.'
    assert exception.value.status_code == HTTPStatus.BAD_REQUEST


def test_change_password_success(valid_user: User, user_service: UserService):
    password = valid_user.password
    valid_user.password = user_service.crypt_service.hash(valid_user.password)
    user_service.user_repository.find_by_id.return_value = valid_user

    user_service.change_password(1, password, '5323')
    
    user_service.user_repository.update.assert_called()


# Delete User Test
def test_delete_user_success(valid_user: User, user_service: UserService):
    user_service.user_repository.find_by_id.return_value = valid_user
    
    user_service.delete(valid_user)
    
    user_service.user_repository.delete.assert_called()
