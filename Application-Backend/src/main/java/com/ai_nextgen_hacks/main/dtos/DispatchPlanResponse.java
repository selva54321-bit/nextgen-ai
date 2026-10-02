package com.ai_nextgen_hacks.main.dtos;

import java.util.List;

public record DispatchPlanResponse(
    String planningId,
    String status,
    String orderId,
    String dispatchUnitId,
    WarehouseInfo warehouse,
    DeliveryInfo delivery
) {
    public record WarehouseInfo(String pickingStatus, boolean dispatchReady) {}
    public record DeliveryInfo(Double failureProbability, String riskBand, List<String> topFactors) {}
}
