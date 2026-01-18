import os
import json
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AIModel:
    """AI模型配置数据类"""
    id: str  # 唯一标识符
    name: str  # 显示名称
    provider: str  # 提供商 (siliconflow, gemini, openai等)
    model_name: str  # 模型名称
    api_key: str  # API密钥
    base_url: Optional[str] = None  # API基础URL（可选）
    description: Optional[str] = None  # 模型描述
    is_active: bool = False  # 是否为当前活动模型

class ModelManager:
    """模型管理器，负责模型的添加、删除、更新、切换等操作"""
    
    _instance: Optional['ModelManager'] = None
    
    def __new__(cls, config_file: str = None):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.__init__(config_file)
        return cls._instance
    
    def __init__(self, config_file: str = None):
        """初始化模型管理器"""
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), '../config/models.json')
        self.models: Dict[str, AIModel] = {}
        self.active_model: Optional[AIModel] = None
        self.load_models()
    
    def load_models(self):
        """从配置文件加载模型列表"""
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 如果文件不存在，创建默认配置
            if not os.path.exists(self.config_file):
                self._create_default_config()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                models_data = json.load(f)
                
            self.models.clear()
            self.active_model = None
            
            for model_data in models_data:
                model = AIModel(**model_data)
                self.models[model.id] = model
                if model.is_active:
                    self.active_model = model
                    # 确保只有一个活动模型
                    for other_model in self.models.values():
                        if other_model.id != model.id:
                            other_model.is_active = False
        
        except Exception as e:
            logger.error(f"Failed to load models from {self.config_file}: {e}")
            # 创建默认配置
            self._create_default_config()
    
    def save_models(self):
        """保存模型列表到配置文件"""
        try:
            # 转换为字典列表
            models_data = [asdict(model) for model in self.models.values()]
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(models_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Models saved to {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save models to {self.config_file}: {e}")
            return False
    
    def _create_default_config(self):
        """创建默认模型配置"""
        try:
            # 创建一个默认的硅基流动模型
            default_model = AIModel(
                id="siliconflow-default",
                name="硅基流动默认模型",
                provider="siliconflow",
                model_name="deepseek-ai/DeepSeek-V3.2",
                api_key="sk-poshxhwkdetphtmmeilfegtrpsnbotwhiomjpxipjrfuqcrv",
                base_url="https://api.siliconflow.cn/v1",
                description="硅基流动提供的DeepSeek V3.2模型",
                is_active=True
            )
            
            self.models[default_model.id] = default_model
            self.active_model = default_model
            
            # 保存默认配置
            self.save_models()
            logger.info(f"Created default model configuration")
            
        except Exception as e:
            logger.error(f"Failed to create default model configuration: {e}")
    
    def add_model(self, model: AIModel) -> bool:
        """添加新模型"""
        try:
            # 检查ID是否已存在
            if model.id in self.models:
                logger.error(f"Model with ID '{model.id}' already exists")
                return False
            
            # 如果这是第一个模型，设置为活动模型
            if not self.models:
                model.is_active = True
                self.active_model = model
            
            self.models[model.id] = model
            return self.save_models()
        
        except Exception as e:
            logger.error(f"Failed to add model: {e}")
            return False
    
    def update_model(self, model_id: str, updated_model: AIModel) -> bool:
        """更新模型配置"""
        try:
            if model_id not in self.models:
                logger.error(f"Model with ID '{model_id}' not found")
                return False
            
            # 保持ID一致
            updated_model.id = model_id
            
            # 如果更新的模型是活动模型，更新active_model引用
            if updated_model.is_active:
                # 取消其他模型的活动状态
                for model in self.models.values():
                    model.is_active = False
                updated_model.is_active = True
                self.active_model = updated_model
            
            self.models[model_id] = updated_model
            return self.save_models()
        
        except Exception as e:
            logger.error(f"Failed to update model: {e}")
            return False
    
    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        try:
            if model_id not in self.models:
                logger.error(f"Model with ID '{model_id}' not found")
                return False
            
            # 如果删除的是活动模型，需要重新设置活动模型
            if self.models[model_id].is_active:
                self.active_model = None
                # 如果还有其他模型，设置第一个为活动模型
                if len(self.models) > 1:
                    first_model_id = next(iter(self.models.keys()))
                    if first_model_id != model_id:
                        self.models[first_model_id].is_active = True
                        self.active_model = self.models[first_model_id]
            
            del self.models[model_id]
            return self.save_models()
        
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return False
    
    def set_active_model(self, model_id: str) -> bool:
        """设置活动模型"""
        try:
            if model_id not in self.models:
                logger.error(f"Model with ID '{model_id}' not found")
                return False
            
            # 取消所有模型的活动状态
            for model in self.models.values():
                model.is_active = False
            
            # 设置新的活动模型
            selected_model = self.models[model_id]
            selected_model.is_active = True
            self.active_model = selected_model
            
            return self.save_models()
        
        except Exception as e:
            logger.error(f"Failed to set active model: {e}")
            return False
    
    def get_model(self, model_id: str) -> Optional[AIModel]:
        """根据ID获取模型"""
        return self.models.get(model_id)
    
    def get_active_model(self) -> Optional[AIModel]:
        """获取当前活动模型"""
        return self.active_model
    
    def get_all_models(self) -> List[AIModel]:
        """获取所有模型列表"""
        return list(self.models.values())
    
    def get_models_by_provider(self, provider: str) -> List[AIModel]:
        """根据提供商获取模型列表"""
        return [model for model in self.models.values() if model.provider == provider]

def get_model_manager(config_file: str = None) -> ModelManager:
    """获取模型管理器实例（工厂函数）"""
    return ModelManager(config_file)