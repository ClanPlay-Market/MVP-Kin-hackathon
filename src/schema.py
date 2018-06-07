from datetime import datetime, timedelta
from enum import Enum
from random import randint

from kin.stellar.utils import is_valid_address, is_valid_transaction_hash
from mongoengine import *
from mongoengine import signals

# noinspection PyUnusedLocal
from config import TOURNEY_URL, TOURNEY_LENGTH
from misc.exceptions import UserAlreadyJoinedError, TourneyTransactionDuplicatedError, WalletAddressError, \
    TransactionHashError, TourneyNotJoinableError


# noinspection PyUnusedLocal
def _set_last_modified(sender, **kwargs):
    doc = kwargs['document']
    doc.last_modified = datetime.utcnow()


class TourneyMemberED(EmbeddedDocument):
    user_id = StringField(required=True)
    alias_id = StringField(required=True)
    name = StringField(required=True)
    tag = StringField(required=True)
    wallet_public_key = StringField(required=True)
    joinedAt = DateTimeField(required=True)
    currentTrophies = IntField(required=True)

    def as_dict(self):
        # noinspection PyTypeChecker
        return {
            'user_id': self.user_id,
            'cpUserId': self.user_id,
            'name': self.name,
            'tag': self.tag,
            'startTrophies': 0,
            'currentTrophies': self.currentTrophies,
            'alias_id': self.alias_id,
            'wallet_public_key': self.wallet_public_key
        }


class TourneyStatus(Enum):
    NOT_PAYED_YET = 'not_payed_yet'
    PAYED = 'payed'
    ENDED = 'ended'
    NOT_PAYED_ERROR = 'not_payed_error'
    PAYMENT_ERROR = 'payment_error'


class Tourney(Document):
    meta = {'collection': 'tourney'}
    name = StringField(required=True)
    description = StringField(required=False)
    prize = FloatField(required=False)
    transaction_id = StringField(required=True)
    user_id = StringField(required=True)
    members = EmbeddedDocumentListField(document_type=TourneyMemberED)
    status = StringField(required=True, choices=[e.value for e in TourneyStatus])
    startAt = DateTimeField(required=True)
    endAt = DateTimeField(required=True)
    payed = DateTimeField(required=False)
    ended = DateTimeField(required=False)
    prize_sent = FloatField(required=False)
    prize_sending_log = StringField(required=False)
    error_message = StringField(required=False)
    fund_address = StringField(required=False)
    last_modified = DateTimeField(required=True)

    def as_dict(self):
        # noinspection PyTypeChecker
        return {
            '_id': self.id,
            'title': self.name,
            'description': self.description,
            'prize': self.prize,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'members': [m.as_dict() for m in sorted(self.members, key=lambda m: m.currentTrophies, reverse=True)],
            'members_count': len(self.members),
            'status': self.status,
            'last_modified': self.last_modified,
            'link': TOURNEY_URL % self.id,
            'startAt': self.startAt,
            'endAt': self.endAt,
            'payed': self.payed,
            'ended': self.ended,
            'prize_sent': self.prize_sent,
            'prize_sending_log': self.prize_sending_log,
            'error_message': self.error_message,
        }

    def join(self, member: dict):
        if self.status not in (TourneyStatus.NOT_PAYED_YET.value, TourneyStatus.PAYED.value):
            raise TourneyNotJoinableError("Tourney is not joinable (status %s)" % self.status)

        if not is_valid_address(member['wallet_public_key']):
            raise WalletAddressError("Wallet address %s is invalid" % member['wallet_public_key'])
        # noinspection PyTypeChecker
        for m in self.members:
            if member['user_id'] == m.user_id:
                raise UserAlreadyJoinedError("User %s is already joined to tourney %s" % (member['user_id'], self.id))
            if member['wallet_public_key'] == m.wallet_public_key:
                raise UserAlreadyJoinedError("User with wallet %s is already joined to tourney %s" % (
                    member['wallet_public_key'], self.id))
        member['joinedAt'] = datetime.utcnow()
        member['currentTrophies'] = randint(-60, 100)
        # noinspection PyUnresolvedReferences
        self.members.create(**member)
        self.save()

    @classmethod
    def create(cls, name, description, prize, transaction_id, user_id):
        if not is_valid_transaction_hash(transaction_id):
            raise TransactionHashError("Transaction hash %s is invalid" % transaction_id)
        if len(Tourney.objects(transaction_id=transaction_id)) > 0:
            raise TourneyTransactionDuplicatedError("Tourney for transaction %s is already created" % transaction_id)

        start_at = datetime.utcnow()
        tourney = Tourney(
            name=name, description=description, prize=prize, transaction_id=transaction_id, user_id=user_id,
            startAt=start_at, endAt=start_at + timedelta(seconds=TOURNEY_LENGTH),
            status=TourneyStatus.NOT_PAYED_YET.value
        )
        tourney.save()
        return tourney


signals.pre_save.connect(_set_last_modified, sender=Tourney)
