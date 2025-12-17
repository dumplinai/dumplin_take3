import 'package:purchases_flutter/purchases_flutter.dart';
import 'dart:io' show Platform;
import 'dart:developer' as developer;

/// Service for initializing and managing RevenueCat SDK.
class RevenueCatService {
  static const String _appleApiKey = 'YOUR_APPLE_API_KEY';
  static const String _googleApiKey = 'YOUR_GOOGLE_API_KEY';

  /// Initialize RevenueCat SDK.
  /// Call this in main() before runApp().
  static Future<void> initialize() async {
    await Purchases.setLogLevel(LogLevel.debug);

    PurchasesConfiguration configuration;
    if (Platform.isIOS) {
      configuration = PurchasesConfiguration(_appleApiKey);
    } else if (Platform.isAndroid) {
      configuration = PurchasesConfiguration(_googleApiKey);
    } else {
      throw UnsupportedError('Platform not supported');
    }

    await Purchases.configure(configuration);
    developer.log('RevenueCat initialized', name: 'RevenueCatService');
  }

  /// Log in user to RevenueCat.
  /// Call this after Firebase authentication.
  static Future<CustomerInfo> logIn(String userId) async {
    final result = await Purchases.logIn(userId);
    developer.log('User logged in to RevenueCat: $userId', name: 'RevenueCatService');
    return result.customerInfo;
  }

  /// Log out user from RevenueCat.
  /// Call this when user signs out.
  static Future<CustomerInfo> logOut() async {
    final info = await Purchases.logOut();
    developer.log('User logged out from RevenueCat', name: 'RevenueCatService');
    return info;
  }

  /// Get current offerings (available subscription products).
  static Future<Offerings> getOfferings() async {
    return await Purchases.getOfferings();
  }

  /// Purchase a package.
  static Future<CustomerInfo> purchasePackage(Package package) async {
    final result = await Purchases.purchasePackage(package);
    developer.log('Package purchased: ${package.identifier}', name: 'RevenueCatService');
    return result.customerInfo;
  }

  /// Get current customer info.
  static Future<CustomerInfo> getCustomerInfo() async {
    return await Purchases.getCustomerInfo();
  }

  /// Restore purchases.
  static Future<CustomerInfo> restorePurchases() async {
    return await Purchases.restorePurchases();
  }
}
