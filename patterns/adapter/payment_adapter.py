"""
Adapter Pattern for integrating external payment systems
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentGateway(ABC):
    """Interface for payment gateway operations"""
    
    @abstractmethod
    def process_payment(self, amount: float, account_id: str, 
                       recipient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment through the gateway"""
        pass


class ExternalPaymentSystem:
    """Simulated external payment system with incompatible interface"""
    
    def make_payment(self, payment_data: Dict[str, str]) -> Dict[str, str]:
        """
        External system method with different signature
        Expects: {'amount': '100.00', 'from_account': 'ACC123', 'to_account': 'ACC456'}
        Returns: {'status': 'success', 'transaction_ref': 'TXN789'}
        """
        # Simulate external API call
        return {
            'status': 'success',
            'transaction_ref': f"EXT_{payment_data.get('from_account')}_{payment_data.get('amount')}"
        }


class PaymentGatewayAdapter(PaymentGateway):
    """Adapter to convert our interface to external system interface"""
    
    def __init__(self, external_system: ExternalPaymentSystem):
        self.external_system = external_system
    
    def process_payment(self, amount: float, account_id: str, 
                       recipient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt our interface to external system"""
        # Convert our format to external system format
        payment_data = {
            'amount': str(amount),
            'from_account': account_id,
            'to_account': recipient_info.get('account_id', ''),
            'recipient_name': recipient_info.get('name', '')
        }
        
        # Call external system
        result = self.external_system.make_payment(payment_data)
        
        # Convert external system response to our format
        return {
            'success': result.get('status') == 'success',
            'transaction_reference': result.get('transaction_ref'),
            'message': f"Payment processed via external gateway: {result.get('transaction_ref')}"
        }


class LegacyBankingAPI:
    """Another external system with different interface"""
    
    def transfer_funds(self, from_acc: str, to_acc: str, amt: float) -> bool:
        """Legacy API method"""
        # Simulate legacy API
        return True


class LegacyBankingAdapter(PaymentGateway):
    """Adapter for legacy banking API"""
    
    def __init__(self, legacy_api: LegacyBankingAPI):
        self.legacy_api = legacy_api
    
    def process_payment(self, amount: float, account_id: str, 
                       recipient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt to legacy API"""
        target_account = recipient_info.get('account_id', '')
        success = self.legacy_api.transfer_funds(account_id, target_account, amount)
        
        return {
            'success': success,
            'transaction_reference': f"LEGACY_{account_id}_{target_account}",
            'message': "Payment processed via legacy banking system"
        }

