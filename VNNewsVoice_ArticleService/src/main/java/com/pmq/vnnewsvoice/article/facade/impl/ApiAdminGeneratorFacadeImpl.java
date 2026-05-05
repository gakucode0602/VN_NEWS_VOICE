package com.pmq.vnnewsvoice.article.facade.impl;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.GeneratorDto;
import com.pmq.vnnewsvoice.article.dto.GeneratorListResponse;
import com.pmq.vnnewsvoice.article.dto.GeneratorRequest;
import com.pmq.vnnewsvoice.article.facade.ApiAdminGeneratorFacade;
import com.pmq.vnnewsvoice.article.mapper.GeneratorMapper;
import com.pmq.vnnewsvoice.article.pojo.Generator;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import com.pmq.vnnewsvoice.article.service.GeneratorService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class ApiAdminGeneratorFacadeImpl implements ApiAdminGeneratorFacade {

  private final GeneratorService generatorService;
  private final ArticleService articleService;
  private final GeneratorMapper generatorMapper;

  @Override
  public ApiResult<GeneratorListResponse> getGenerators(Map<String, String> params) {
    long totalItems = generatorService.countSearchGenerators(params);
    List<Generator> list = generatorService.getGenerators(params);
    List<GeneratorDto> dtos = list.stream().map(generatorMapper::toDto).toList();

    int page = Integer.parseInt(params.getOrDefault("page", "1"));
    int pageSize = Integer.parseInt(params.getOrDefault("pageSize", "10"));
    int totalPages = totalItems == 0 ? 1 : (int) Math.ceil((double) totalItems / pageSize);

    GeneratorListResponse res =
        GeneratorListResponse.builder()
            .generators(dtos)
            .totalItems(totalItems)
            .currentPage(page)
            .totalPages(totalPages)
            .startIndex(dtos.isEmpty() ? 0 : (page - 1) * pageSize + 1)
            .endIndex(Math.min(page * pageSize, (int) totalItems))
            .build();

    return ApiResult.success(HttpStatus.OK, res);
  }

  @Override
  public ApiResult<GeneratorDto> addGenerator(GeneratorRequest request) {
    Generator gen = new Generator();
    gen.setName(request.getName());
    gen.setUrl(request.getUrl());
    gen.setLogoUrl(request.getLogoUrl());
    gen.setRssUrl(request.getRssUrl());
    gen.setCrawlIntervalMinutes(
        request.getCrawlIntervalMinutes() != null ? request.getCrawlIntervalMinutes() : 60);
    gen.setIsActive(request.getIsActive() != null ? request.getIsActive() : true);

    Generator saved = generatorService.addGenerator(gen);
    if (saved != null) {
      return ApiResult.success(
          HttpStatus.CREATED, generatorMapper.toDto(saved), "Tạo generator thành công");
    }
    return ApiResult.failure(HttpStatus.BAD_REQUEST, "Lỗi tạo cấu hình Crawl");
  }

  @Override
  public ApiResult<GeneratorDto> updateGenerator(Long id, GeneratorRequest request) {
    Optional<Generator> opt = generatorService.getGeneratorById(id);
    if (opt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy generator");
    }
    Generator gen = opt.get();
    gen.setName(request.getName());
    gen.setUrl(request.getUrl());
    gen.setLogoUrl(request.getLogoUrl());
    gen.setRssUrl(request.getRssUrl());

    if (request.getCrawlIntervalMinutes() != null) {
      gen.setCrawlIntervalMinutes(request.getCrawlIntervalMinutes());
    }
    if (request.getIsActive() != null) {
      gen.setIsActive(request.getIsActive());
    }

    Optional<Generator> updatedOpt = generatorService.updateGenerator(gen);
    if (updatedOpt.isPresent()) {
      return ApiResult.success(
          HttpStatus.OK, generatorMapper.toDto(updatedOpt.get()), "Cập nhật thành công");
    }
    return ApiResult.failure(HttpStatus.BAD_REQUEST, "Lỗi cập nhật cấu hình Crawl");
  }

  @Override
  public ApiResult<Void> toggleGeneratorStatus(Long id) {
    Optional<Generator> opt = generatorService.getGeneratorById(id);
    if (opt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy generator");
    }
    Generator gen = opt.get();
    gen.setIsActive(!gen.getIsActive());
    generatorService.updateGenerator(gen);
    return ApiResult.success(HttpStatus.OK, null, "Đã cập nhật trạng thái hoạt động");
  }

  @Override
  public ApiResult<Void> deleteGenerator(Long id) {
    Map<String, String> filters = new HashMap<>();
    filters.put("generatorId", id.toString());
    long count = articleService.countSearchArticles(filters);

    if (count > 0) {
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST, "Không thể xóa cấu hình đang có bài báo liên kết");
    }

    boolean deleted = generatorService.deleteGenerator(id);
    if (deleted) {
      return ApiResult.success(HttpStatus.OK, null, "Xóa cấu hình thành công");
    }
    return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Lỗi xóa generator");
  }
}
