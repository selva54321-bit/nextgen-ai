package com.ai_nextgen_hacks.main.config;

import com.ai_nextgen_hacks.main.models.DispatchUnit;
import com.ai_nextgen_hacks.main.models.Order;
import com.ai_nextgen_hacks.main.repos.DispatchUnitRepository;
import com.ai_nextgen_hacks.main.repos.OrderRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.LocalDateTime;

@Configuration
public class DatabaseSeeder {

    @Bean
    public CommandLineRunner initData(OrderRepository orderRepository, DispatchUnitRepository dispatchUnitRepository) {
        return args -> {
            if (orderRepository.count() == 0) {
                Order order1 = new Order("ORD-1042", "CUST-001", LocalDateTime.now(), "PENDING", LocalDateTime.now().plusDays(2));
                orderRepository.save(order1);
                
                DispatchUnit unit1 = new DispatchUnit();
                unit1.setUnitId("DU-03");
                unit1.setCapacity(100.0);
                unit1.setAvailability("AVAILABLE");
                unit1.setCurrentLocation("ZONE-A");
                dispatchUnitRepository.save(unit1);
                
                System.out.println("Mock data seeded!");
            }
        };
    }
}
