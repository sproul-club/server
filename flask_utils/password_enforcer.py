from password_strength import PasswordPolicy

class PasswordEnforcer:
    # A convenience constructor for initializing the password strength enforcer
    def __init__(self):
        self.pass_policy = PasswordPolicy.from_names(
            length=8,     # min length: 8
            numbers=1,    # need min. 1 digits
            special=1    # need min. 1 special characters
        )

    # Check if the password is strong enough or not
    def check(self, password):
        errors = self.pass_policy.test(password)
        return len(errors) == 0
