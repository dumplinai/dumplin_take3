import 'package:get/get.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'dart:developer' as developer;

/// Controller for managing RevenueCat subscription state.
///
/// This controller handles:
/// - Checking subscription status
/// - Listening for real-time subscription updates via CustomerInfo listener
/// - Managing pro entitlement state
class SubscriptionController extends GetxController {
  static const String entitlementId = 'pro';

  // Observable subscription state
  final RxBool isPro = false.obs;
  final RxBool isLoading = true.obs;
  final Rx<CustomerInfo?> customerInfo = Rx<CustomerInfo?>(null);
  final Rx<DateTime?> expirationDate = Rx<DateTime?>(null);
  final RxString currentProductId = ''.obs;

  @override
  void onInit() {
    super.onInit();
    _initializeSubscription();

    // Add CustomerInfo listener for real-time updates
    Purchases.addCustomerInfoUpdateListener(_onCustomerInfoUpdate);
  }

  @override
  void onClose() {
    // Remove listener when controller is disposed
    Purchases.removeCustomerInfoUpdateListener(_onCustomerInfoUpdate);
    super.onClose();
  }

  /// Initialize subscription status on app start.
  Future<void> _initializeSubscription() async {
    isLoading.value = true;
    try {
      await _checkSubscriptionStatus();
    } catch (e) {
      developer.log('Error initializing subscription: $e', name: 'SubscriptionController');
    } finally {
      isLoading.value = false;
    }
  }

  /// Callback for CustomerInfo updates from RevenueCat.
  /// This is called whenever subscription status changes.
  void _onCustomerInfoUpdate(CustomerInfo info) {
    developer.log('CustomerInfo updated', name: 'SubscriptionController');
    _updateSubscriptionState(info);
  }

  /// Check current subscription status from RevenueCat.
  Future<void> _checkSubscriptionStatus() async {
    try {
      final info = await Purchases.getCustomerInfo();
      _updateSubscriptionState(info);
    } catch (e) {
      developer.log('Error checking subscription status: $e', name: 'SubscriptionController');
      isPro.value = false;
    }
  }

  /// Update subscription state from CustomerInfo.
  void _updateSubscriptionState(CustomerInfo info) {
    customerInfo.value = info;

    // Check if user has pro entitlement
    final entitlement = info.entitlements.active[entitlementId];
    isPro.value = entitlement != null;

    if (entitlement != null) {
      // Update expiration date
      if (entitlement.expirationDate != null) {
        expirationDate.value = DateTime.parse(entitlement.expirationDate!);
      }

      // Update product ID
      currentProductId.value = entitlement.productIdentifier;

      developer.log(
        'Pro subscription active: ${entitlement.productIdentifier}, expires: ${entitlement.expirationDate}',
        name: 'SubscriptionController',
      );
    } else {
      expirationDate.value = null;
      currentProductId.value = '';
      developer.log('No active pro subscription', name: 'SubscriptionController');
    }
  }

  /// Refresh subscription status manually.
  /// Call this after a purchase or when needed.
  Future<void> refreshSubscriptionStatus() async {
    isLoading.value = true;
    try {
      await _checkSubscriptionStatus();
    } finally {
      isLoading.value = false;
    }
  }

  /// Restore purchases from app stores.
  Future<bool> restorePurchases() async {
    isLoading.value = true;
    try {
      final info = await Purchases.restorePurchases();
      _updateSubscriptionState(info);
      return isPro.value;
    } catch (e) {
      developer.log('Error restoring purchases: $e', name: 'SubscriptionController');
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  /// Check if subscription is expiring soon (within 7 days).
  bool get isExpiringSoon {
    if (!isPro.value || expirationDate.value == null) return false;
    final daysUntilExpiration = expirationDate.value!.difference(DateTime.now()).inDays;
    return daysUntilExpiration <= 7 && daysUntilExpiration > 0;
  }

  /// Get days until subscription expires.
  int? get daysUntilExpiration {
    if (!isPro.value || expirationDate.value == null) return null;
    return expirationDate.value!.difference(DateTime.now()).inDays;
  }
}
