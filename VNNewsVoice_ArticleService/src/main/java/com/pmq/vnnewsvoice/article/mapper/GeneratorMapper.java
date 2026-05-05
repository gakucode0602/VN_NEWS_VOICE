package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.GeneratorDto;
import com.pmq.vnnewsvoice.article.pojo.Generator;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface GeneratorMapper {
  GeneratorDto toDto(Generator generator);
}
