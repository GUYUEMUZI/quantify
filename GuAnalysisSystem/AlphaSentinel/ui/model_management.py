import streamlit as st
import uuid
from analysis.model_manager import get_model_manager, AIModel


def render_model_management():
    """渲染模型管理界面"""
    model_manager = get_model_manager()
    
    # 创建三列布局
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("#### 当前模型")
        active_model = model_manager.get_active_model()
        if active_model:
            st.info(f"**{active_model.name}**\n\n提供商: {active_model.provider}\n\n模型: {active_model.model_name}")
        else:
            st.warning("未设置活动模型")
    
    with col2:
        st.markdown("#### 模型选择")
        models = model_manager.get_all_models()
        
        if models:
            # 创建模型选择下拉菜单
            model_options = {model.name: model.id for model in models}
            selected_model_name = st.selectbox(
                "选择模型",
                options=list(model_options.keys()),
                format_func=lambda x: x
            )
            
            selected_model_id = model_options[selected_model_name]
            
            # 设置为活动模型按钮
            if st.button("设为当前模型"):
                if model_manager.set_active_model(selected_model_id):
                    st.success(f"已将 {selected_model_name} 设置为当前模型")
                    st.rerun()
                else:
                    st.error("设置模型失败")
        else:
            st.warning("暂无可用模型")
    
    with col3:
        st.markdown("#### 模型操作")
        
        # 添加模型按钮
        if st.button("添加新模型"):
            st.session_state["show_add_model"] = True
            st.session_state["show_edit_model"] = False
        
        # 编辑模型按钮
        models = model_manager.get_all_models()
        if models:
            edit_model_options = {model.name: model.id for model in models}
            selected_edit_model_name = st.selectbox(
                "编辑模型",
                options=list(edit_model_options.keys()),
                format_func=lambda x: x,
                key="edit_model_select"
            )
            
            if st.button("编辑选中模型"):
                st.session_state["edit_model_id"] = edit_model_options[selected_edit_model_name]
                st.session_state["show_edit_model"] = True
                st.session_state["show_add_model"] = False


def render_add_model_form():
    """渲染添加模型表单"""
    st.subheader("添加新模型")
    
    with st.form("add_model_form"):
        # 基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("模型显示名称")
            provider = st.selectbox(
                "提供商",
                options=["siliconflow", "gemini", "openai"],
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            model_name = st.text_input("模型名称")
            api_key = st.text_input("API密钥", type="password")
        
        # 高级设置
        with st.expander("高级设置"):
            base_url = st.text_input("API基础URL")
            description = st.text_area("模型描述")
        
        # 提交按钮
        submit_button = st.form_submit_button("添加模型")
        
        if submit_button:
            if not all([name, provider, model_name, api_key]):
                st.error("请填写所有必填字段")
                return
            
            # 创建模型对象
            model_id = str(uuid.uuid4())[:8]  # 生成短UUID作为ID
            model = AIModel(
                id=model_id,
                name=name,
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url if base_url else None,
                description=description if description else None,
                is_active=False
            )
            
            # 添加模型
            model_manager = get_model_manager()
            if model_manager.add_model(model):
                st.success(f"模型 {name} 添加成功")
                # 清除表单状态
                st.session_state["show_add_model"] = False
                st.rerun()
            else:
                st.error("模型添加失败")


def render_edit_model_form():
    """渲染编辑模型表单"""
    model_manager = get_model_manager()
    model_id = st.session_state.get("edit_model_id")
    
    if not model_id:
        st.warning("未选择要编辑的模型")
        return
    
    model = model_manager.get_model(model_id)
    
    if not model:
        st.error("未找到指定模型")
        return
    
    st.subheader(f"编辑模型: {model.name}")
    
    with st.form("edit_model_form"):
        # 基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("模型显示名称", value=model.name)
            provider = st.selectbox(
                "提供商",
                options=["siliconflow", "gemini", "openai"],
                index=["siliconflow", "gemini", "openai"].index(model.provider),
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            model_name = st.text_input("模型名称", value=model.model_name)
            api_key = st.text_input("API密钥", value=model.api_key, type="password")
        
        # 高级设置
        with st.expander("高级设置"):
            base_url = st.text_input("API基础URL", value=model.base_url or "")
            description = st.text_area("模型描述", value=model.description or "")
        
        # 提交按钮
        col_save, col_delete = st.columns(2)
        
        with col_save:
            submit_button = st.form_submit_button("保存修改")
        
        with col_delete:
            delete_button = st.form_submit_button("删除模型", type="primary", use_container_width=True)
        
        if submit_button:
            if not all([name, provider, model_name, api_key]):
                st.error("请填写所有必填字段")
                return
            
            # 更新模型对象
            updated_model = AIModel(
                id=model.id,
                name=name,
                provider=provider,
                model_name=model_name,
                api_key=api_key,
                base_url=base_url if base_url else None,
                description=description if description else None,
                is_active=model.is_active
            )
            
            # 保存修改
            if model_manager.update_model(model.id, updated_model):
                st.success(f"模型 {name} 更新成功")
                st.session_state["show_edit_model"] = False
                st.rerun()
            else:
                st.error("模型更新失败")
        
        if delete_button:
            if model_manager.delete_model(model.id):
                st.success(f"模型 {model.name} 已删除")
                st.session_state["show_edit_model"] = False
                st.rerun()
            else:
                st.error("模型删除失败")


def render_model_details(model_id: str):
    """渲染模型详情"""
    model_manager = get_model_manager()
    model = model_manager.get_model(model_id)
    
    if not model:
        st.error("未找到指定模型")
        return
    
    st.subheader(f"模型详情: {model.name}")
    
    # 显示模型信息
    info_cols = st.columns(2)
    
    with info_cols[0]:
        st.markdown(f"**ID:** {model.id}")
        st.markdown(f"**提供商:** {model.provider}")
        st.markdown(f"**模型名称:** {model.model_name}")
        st.markdown(f"**状态:** {'当前模型' if model.is_active else '可用模型'}")
    
    with info_cols[1]:
        if model.base_url:
            st.markdown(f"**API地址:** {model.base_url}")
        if model.description:
            st.markdown(f"**描述:** {model.description}")
    
    # API密钥（部分隐藏）
    if model.api_key:
        masked_api_key = model.api_key[:4] + "*" * (len(model.api_key) - 4)
        st.markdown(f"**API密钥:** {masked_api_key}")