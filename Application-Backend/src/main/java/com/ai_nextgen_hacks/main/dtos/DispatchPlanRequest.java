package com.ai_nextgen_hacks.main.dtos;

import java.util.List;

public record DispatchPlanRequest(List<String> orderIds, String dispatchUnitId, boolean simulationMode) {}
