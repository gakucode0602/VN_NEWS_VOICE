package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.GeneratorDto;
import com.pmq.vnnewsvoice.article.mapper.GeneratorMapper;
import com.pmq.vnnewsvoice.article.pojo.Generator;
import com.pmq.vnnewsvoice.article.service.GeneratorService;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiGeneratorController {
  private final GeneratorMapper generatorMapper;
  private final GeneratorService generatorService;

  @GetMapping("/generators")
  public ResponseEntity<ApiResponse<List<GeneratorDto>>> getGeneratorList(
      @RequestParam Map<String, String> params) {
    List<Generator> generators = generatorService.getGenerators(params);
    List<GeneratorDto> generatorDtos = generators.stream().map(generatorMapper::toDto).toList();
    return ResponseEntity.ok(
        ApiResponse.<List<GeneratorDto>>builder()
            .success(true)
            .code(HttpStatus.OK.value())
            .result(generatorDtos)
            .build());
  }
}
