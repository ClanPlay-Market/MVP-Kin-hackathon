class UserError(Exception):
    pass


class UserAlreadyJoinedError(UserError):
    pass


class TourneyTransactionDuplicatedError(UserError):
    pass


class WalletAddressError(UserError):
    pass


class TourneyNotJoinableError(UserError):
    pass


class TransactionHashError(UserError):
    pass
