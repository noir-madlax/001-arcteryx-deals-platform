export const PRO_ENTITLEMENT_ID = 'Pro';

export const PRO_PRODUCT_IDS = {
  monthly: 'dev.100app.geardrop.pro.monthly',
  annual: 'dev.100app.geardrop.pro.annual',
  lifetime: 'dev.100app.geardrop.pro.lifetime',
} as const;

export type ProPlanId = keyof typeof PRO_PRODUCT_IDS;

export type ProPlan = {
  id: ProPlanId;
  productId: string;
  price: string;
  pricePerMonth: string | null;
  trialDays: number | null;
};

type ProductLike = {
  identifier: string;
  priceString: string;
  pricePerMonthString: string | null;
  introPrice: {
    price: number;
    period: string;
  } | null;
};

export type PackageLike = {
  identifier: string;
  product: ProductLike;
};

type OfferingLike<TPackage extends PackageLike> = {
  monthly: TPackage | null;
  annual: TPackage | null;
  lifetime: TPackage | null;
  availablePackages: TPackage[];
};

type IntroEligibilityLike = {
  status: number;
};

type CustomerInfoLike = {
  entitlements: {
    active: Record<string, unknown>;
  };
};

export type ProPlanEntry<TPackage extends PackageLike> = {
  plan: ProPlan;
  purchasePackage: TPackage;
};

const PLAN_ORDER: ProPlanId[] = ['monthly', 'annual', 'lifetime'];
const INTRO_ELIGIBLE = 2;

export function hasProEntitlement(customerInfo: CustomerInfoLike) {
  return Boolean(customerInfo.entitlements.active[PRO_ENTITLEMENT_ID]);
}

export function buildProPlanEntries<TPackage extends PackageLike>(
  offering: OfferingLike<TPackage>,
  eligibility: Record<string, IntroEligibilityLike> = {},
): ProPlanEntry<TPackage>[] {
  return PLAN_ORDER.flatMap((id) => {
    const expectedProductId = PRO_PRODUCT_IDS[id];
    const standardPackage = offering[id];
    const purchasePackage = standardPackage?.product.identifier === expectedProductId
      ? standardPackage
      : offering.availablePackages.find((candidate) => candidate.product.identifier === expectedProductId);

    if (!purchasePackage) return [];

    const intro = purchasePackage.product.introPrice;
    const trialDays = eligibility[expectedProductId]?.status === INTRO_ELIGIBLE && intro?.price === 0
      ? parseIsoDays(intro.period)
      : null;

    return [{
      plan: {
        id,
        productId: expectedProductId,
        price: purchasePackage.product.priceString,
        pricePerMonth: purchasePackage.product.pricePerMonthString,
        trialDays,
      },
      purchasePackage,
    }];
  });
}

function parseIsoDays(period: string) {
  const match = /^P(\d+)D$/.exec(period);
  return match ? Number(match[1]) : null;
}
