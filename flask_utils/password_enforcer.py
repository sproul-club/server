from password_strength import PasswordPolicy


class PasswordEnforcer:
    """
    This class provides an easy way to enforce a minimum password strength via the 'password_strength' library.

    Example:

    pass_enforcer = PasswordEnforcer()

    strong_password = 'b1ackp1nk_fanb0y'
    weak_password   = 'btsfangirl'

    pass_enforcer.check(strong_password) # will return True
    pass_enforcer.check(weak_password)   # will return False
    """

    def __init__(self):
        """
        A convenience constructor for initializing the password strength enforcer.
        """

        self.pass_policy = PasswordPolicy.from_names(
            length=8,   # min length: 8
            numbers=1,  # need min. 1 digits
            special=1   # need min. 1 special characters
        )


    def check(self, password):
        """
        Check if the password is strong enough or not given the password policy.
        """
        
        errors = self.pass_policy.test(password)
        return len(errors) == 0
