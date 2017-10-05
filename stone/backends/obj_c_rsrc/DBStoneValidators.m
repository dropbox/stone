///
/// Copyright (c) 2016 Dropbox, Inc. All rights reserved.
///

#import "DBStoneValidators.h"

@implementation DBStoneValidators

+ (void (^)(NSString *))stringValidator:(NSNumber *)minLength
                              maxLength:(NSNumber *)maxLength
                                pattern:(NSString *)pattern {

  void (^validator)(NSString *) = ^(NSString *value) {
    if (minLength != nil) {
      if ([value length] < [minLength unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at least %@ characters", value, [minLength stringValue]];
      }
    }

    if (maxLength != nil) {
      if ([value length] > [maxLength unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at most %@ characters", value, [minLength stringValue]];
      }
    }

    if (pattern != nil && pattern.length != 0) {
      NSError *error;
      NSRegularExpression *re = [NSRegularExpression regularExpressionWithPattern:pattern options:0 error:&error];
      NSArray *matches = [re matchesInString:value options:0 range:NSMakeRange(0, [value length])];
      if ([matches count] == 0) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must match pattern \"%@\"", value, [re pattern]];
      }
    }
  };

  return validator;
}

+ (void (^)(NSNumber *))numericValidator:(NSNumber *)minValue maxValue:(NSNumber *)maxValue {
  void (^validator)(NSNumber *) = ^(NSNumber *value) {
    if (minValue != nil) {
      if ([value unsignedIntegerValue] < [minValue unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at least %@", value, [minValue stringValue]];
      }
    }

    if (maxValue != nil) {
      if ([value unsignedIntegerValue] > [maxValue unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at most %@", value, [maxValue stringValue]];
      }
    }
  };

  return validator;
}

+ (void (^)(NSArray<id> *))arrayValidator:(NSNumber *)minItems
                                 maxItems:(NSNumber *)maxItems
                            itemValidator:(void (^)(id))itemValidator {
  void (^validator)(NSArray<id> *) = ^(NSArray<id> *value) {
    if (minItems != nil) {
      if ([value count] < [minItems unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at least %@ items", value, [minItems stringValue]];
      }
    }

    if (maxItems != nil) {
      if ([value count] > [maxItems unsignedIntegerValue]) {
        [NSException raise:@"IllegalStateException" format:@"\"%@\" must be at most %@ items", value, [maxItems stringValue]];
      }
    }

    if (itemValidator != nil) {
      for (id item in value) {
        itemValidator(item);
      }
    }
  };

  return validator;
}

+ (void (^)(NSDictionary<NSString *, id> *))mapValidator:(void (^)(id))itemValidator {
  void (^validator)(NSDictionary<NSString *, id> *) = ^(NSDictionary<NSString *, id> *value) {
    if (itemValidator != nil) {
      for (id key in value) {
        itemValidator(value[key]);
      }
    }
  };

  return validator;
}

+ (void (^)(id))nullableValidator:(void (^)(id))internalValidator {
  void (^validator)(id) = ^(id value) {
    if (value != nil) {
      internalValidator(value);
    }
  };

  return validator;
}

+ (void (^)(id))nonnullValidator:(void (^)(id))internalValidator {
  void (^validator)(id) = ^(id value) {
    if (value == nil) {
      [NSException raise:@"IllegalStateException" format:@"\"%@\" must not be `nil`.", value];
    }

    if (internalValidator != nil) {
      internalValidator(value);
    }
  };

  return validator;
}

@end
