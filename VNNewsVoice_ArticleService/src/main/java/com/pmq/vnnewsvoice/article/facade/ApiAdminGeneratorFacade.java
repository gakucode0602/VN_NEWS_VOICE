package com.pmq.vnnewsvoice.article.facade;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.GeneratorDto;
import com.pmq.vnnewsvoice.article.dto.GeneratorListResponse;
import com.pmq.vnnewsvoice.article.dto.GeneratorRequest;
import java.util.Map;

public interface ApiAdminGeneratorFacade {
  ApiResult<GeneratorListResponse> getGenerators(Map<String, String> params);

  ApiResult<GeneratorDto> addGenerator(GeneratorRequest request);

  ApiResult<GeneratorDto> updateGenerator(Long id, GeneratorRequest request);

  ApiResult<Void> toggleGeneratorStatus(Long id);

  ApiResult<Void> deleteGenerator(Long id);
}
