package com.ai_nextgen_hacks.main;

import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;

import com.ai_nextgen_hacks.main.dtos.DispatchPlanRequest;
import com.ai_nextgen_hacks.main.dtos.DispatchPlanResponse;
import com.ai_nextgen_hacks.main.models.DispatchUnit;
import com.ai_nextgen_hacks.main.models.Order;
import com.ai_nextgen_hacks.main.repos.DispatchAssignmentRepository;
import com.ai_nextgen_hacks.main.repos.DispatchUnitRepository;
import com.ai_nextgen_hacks.main.repos.OrderRepository;
import com.ai_nextgen_hacks.main.services.DispatchService;
import com.ai_nextgen_hacks.main.services.DataIngestionService;
import org.springframework.mock.web.MockMultipartFile;

import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class AiNextGenHacksApplicationTests {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private DispatchUnitRepository dispatchUnitRepository;

    @Mock
    private DispatchAssignmentRepository dispatchAssignmentRepository;

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private DispatchService dispatchService;

    @Test
    void testDispatchPlan() {
        // Since we want to test real REST calls, we will instantiate a real RestTemplate
        // instead of the mocked one.
        dispatchService = new DispatchService();
        
        // Use reflection or direct assignment if possible, but Autowired fields can be set via Spring ReflectionTestUtils
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "orderRepository", orderRepository);
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "dispatchUnitRepository", dispatchUnitRepository);
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "dispatchAssignmentRepository", dispatchAssignmentRepository);
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "restTemplate", new RestTemplate());

        Order dummyOrder = new Order();
        dummyOrder.setOrderId("ORD-1042");
        Mockito.when(orderRepository.findById("ORD-1042")).thenReturn(Optional.of(dummyOrder));

        DispatchUnit dummyUnit = new DispatchUnit();
        dummyUnit.setUnitId("DU-03");
        Mockito.when(dispatchUnitRepository.findById("DU-03")).thenReturn(Optional.of(dummyUnit));

        DispatchPlanRequest request = new DispatchPlanRequest(List.of("ORD-1042"), "DU-03", true);
        
        DispatchPlanResponse response = dispatchService.planDispatch(request);
        
        System.out.println("==================================================");
        System.out.println("TEST COMPLETED. RESPONSE:");
        System.out.println(response);
        System.out.println("==================================================");
    }

    @Test
    void testDispatchPlanBatch() throws Exception {
        String csvData = "RouteID,StationCode,Date,ZoneID,ExecutorCapacity,Stops,RouteNumPackages,StopTotalVolume,StopAvgVolume,PlannedServiceTime,HasTimeWindow,Val1,Val2,Val3,Val4,Val5\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-24.2B,174,264,1,10440.234,10440.234,60,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-24.1E,174,264,1,10440.234,10440.234,53,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-24.1B,174,264,2,6860.012,3430.006,105,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-23.1G,174,264,2,9556.176,4778.088,48,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-24.3G,174,264,2,59889.452,29944.726,131,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-24.3C,174,264,1,2665.87199,2665.87199,111,0,0,0,0,6,26-08-2018\n" +
            "RouteID_07DSE5,3313071,26-08-2018,B-23.1G,174,264,1,5741.924,5741.924,26,0,0,0,0,6,26-08-2018";

        MockMultipartFile file = new MockMultipartFile("file", "test_batch.csv", "text/csv", csvData.getBytes());
        DataIngestionService dataIngestionService = new DataIngestionService();
        List<String[]> rows = dataIngestionService.processFile(file);

        dispatchService = new DispatchService();
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "restTemplate", new RestTemplate());
        org.springframework.test.util.ReflectionTestUtils.setField(dispatchService, "dispatchAssignmentRepository", dispatchAssignmentRepository);

        System.out.println("================= BATCH TEST START =================");
        for (String[] row : rows) {
            DispatchPlanResponse response = dispatchService.planDispatchDynamic(row);
            System.out.println("Processed row for ZoneID: " + row[3]);
            System.out.println(response);
            System.out.println("--------------------------------------------------");
        }
        System.out.println("================== BATCH TEST END ==================");
    }
}

