"""
Unit tests for resource management module.
"""

from unittest.mock import MagicMock, patch

import pytest

from awslabs.ecs_mcp_server.api.resource_management import (
    describe_capacity_provider,
    describe_cluster,
    describe_container_instance,
    describe_service,
    describe_task,
    describe_task_definition,
    ecs_resource_management,
    list_capacity_providers,
    list_clusters,
    list_container_instances,
    list_services,
    list_task_definitions,
    list_tasks,
)

# ----------------------------------------------------------------------------
# Main Resource Management Function Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_describe_cluster(mock_get_client):
    """Test ecs_resource_management function with describe_cluster action."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_clusters.return_value = {
        "clusters": [{"clusterName": "test-cluster", "status": "ACTIVE"}]
    }
    mock_ecs.list_services.return_value = {"serviceArns": ["service-1"]}
    mock_ecs.list_tasks.side_effect = [
        {"taskArns": ["task-1"]},  # Running tasks
        {"taskArns": []},  # Stopped tasks
    ]
    mock_get_client.return_value = mock_ecs

    # Call ecs_resource_management with describe_cluster action
    result = await ecs_resource_management(
        action="describe", resource_type="cluster", identifier="test-cluster"
    )

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_clusters was called with correct parameters
    mock_ecs.describe_clusters.assert_called_once_with(
        clusters=["test-cluster"], include=["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]
    )

    # Verify the result
    assert result["cluster"]["clusterName"] == "test-cluster"
    assert result["service_count"] == 1
    assert result["task_count"] == 1
    assert result["running_task_count"] == 1


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_list_services(mock_get_client):
    """Test ecs_resource_management function with list_services action."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    # Mock paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"serviceArns": ["service-1", "service-2"]}]
    mock_ecs.get_paginator.return_value = mock_paginator

    mock_ecs.describe_services.return_value = {
        "services": [
            {"serviceName": "service-1", "status": "ACTIVE"},
            {"serviceName": "service-2", "status": "ACTIVE"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call ecs_resource_management with list_services action
    result = await ecs_resource_management(
        action="list", resource_type="service", filters={"cluster": "test-cluster"}
    )

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify get_paginator was called
    mock_ecs.get_paginator.assert_called_once_with("list_services")

    # Verify paginator.paginate was called with correct cluster
    mock_paginator.paginate.assert_called_once_with(cluster="test-cluster")

    # Verify describe_services was called with correct parameters
    mock_ecs.describe_services.assert_called_once_with(
        cluster="test-cluster", services=["service-1", "service-2"], include=["TAGS"]
    )

    # Verify the result
    assert len(result["services"]) == 2
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_describe_service(mock_get_client):
    """Test ecs_resource_management function with describe_service action."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_services.return_value = {
        "services": [{"serviceName": "test-service", "status": "ACTIVE", "events": []}]
    }
    mock_ecs.list_tasks.side_effect = [
        {"taskArns": ["task-1"]},  # Running tasks
        {"taskArns": []},  # Stopped tasks
    ]
    mock_get_client.return_value = mock_ecs

    # Call ecs_resource_management with describe_service action
    result = await ecs_resource_management(
        action="describe",
        resource_type="service",
        identifier="test-service",
        filters={"cluster": "test-cluster"},
    )

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_services was called with correct parameters
    mock_ecs.describe_services.assert_called_once_with(
        cluster="test-cluster", services=["test-service"], include=["TAGS"]
    )

    # Verify the result
    assert result["service"]["serviceName"] == "test-service"
    assert result["running_task_count"] == 1
    assert result["stopped_task_count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_describe_service_missing_cluster(mock_get_client):
    """Test ecs_resource_management function with describe_service action and missing cluster."""
    # Call ecs_resource_management with describe_service action and no cluster
    with pytest.raises(ValueError) as excinfo:
        await ecs_resource_management(
            action="describe", resource_type="service", identifier="test-service"
        )

    # Verify the error message
    assert "Cluster filter is required" in str(excinfo.value)


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_invalid_action(mock_get_client):
    """Test ecs_resource_management function with invalid action."""
    # Call ecs_resource_management with invalid action
    with pytest.raises(ValueError) as excinfo:
        await ecs_resource_management(action="invalid", resource_type="cluster")

    # Verify the error message
    assert "Unsupported action" in str(excinfo.value)


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_invalid_resource_type(mock_get_client):
    """Test ecs_resource_management function with invalid resource type."""
    # Call ecs_resource_management with invalid resource type
    with pytest.raises(ValueError) as excinfo:
        await ecs_resource_management(action="list", resource_type="invalid")

    # Verify the error message
    assert "Unsupported resource type" in str(excinfo.value)


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_describe_missing_identifier(mock_get_client):
    """Test ecs_resource_management function with describe action and missing identifier."""
    # Call ecs_resource_management with describe action and no identifier
    with pytest.raises(ValueError) as excinfo:
        await ecs_resource_management(action="describe", resource_type="cluster")

    # Verify the error message
    assert "Identifier is required" in str(excinfo.value)


# ----------------------------------------------------------------------------
# Main Resource Management Function Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_ecs_resource_management_list_clusters(mock_get_client):
    """Test ecs_resource_management function with list_clusters action."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_clusters.return_value = {"clusterArns": ["cluster-1", "cluster-2"]}
    mock_ecs.describe_clusters.return_value = {
        "clusters": [
            {"clusterName": "cluster-1", "status": "ACTIVE"},
            {"clusterName": "cluster-2", "status": "ACTIVE"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call ecs_resource_management with list_clusters action
    result = await ecs_resource_management(action="list", resource_type="cluster")

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify the result
    assert len(result["clusters"]) == 2
    assert result["count"] == 2


# ----------------------------------------------------------------------------
# Cluster Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_clusters(mock_get_client):
    """Test list_clusters function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_clusters.return_value = {"clusterArns": ["cluster-1", "cluster-2"]}
    mock_ecs.describe_clusters.return_value = {
        "clusters": [
            {"clusterName": "cluster-1", "status": "ACTIVE"},
            {"clusterName": "cluster-2", "status": "ACTIVE"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call list_clusters
    result = await list_clusters({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify the result
    assert len(result["clusters"]) == 2
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_clusters_empty(mock_get_client):
    """Test list_clusters function with empty response."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_clusters.return_value = {"clusterArns": []}
    mock_get_client.return_value = mock_ecs

    # Call list_clusters
    result = await list_clusters({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify the result
    assert result["clusters"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_clusters_error(mock_get_client):
    """Test list_clusters function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_clusters.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call list_clusters
    result = await list_clusters({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify the result
    assert "error" in result
    assert result["clusters"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_cluster(mock_get_client):
    """Test describe_cluster function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_clusters.return_value = {
        "clusters": [{"clusterName": "test-cluster", "status": "ACTIVE"}]
    }
    mock_ecs.list_services.return_value = {"serviceArns": ["service-1"]}
    mock_ecs.list_tasks.side_effect = [
        {"taskArns": ["task-1"]},  # Running tasks
        {"taskArns": []},  # Stopped tasks
    ]
    mock_get_client.return_value = mock_ecs

    # Call describe_cluster
    result = await describe_cluster("test-cluster", {})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_clusters was called with correct cluster
    mock_ecs.describe_clusters.assert_called_once_with(
        clusters=["test-cluster"], include=["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]
    )

    # Verify the result
    assert result["cluster"]["clusterName"] == "test-cluster"
    assert result["service_count"] == 1
    assert result["task_count"] == 1
    assert result["running_task_count"] == 1


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_cluster_not_found(mock_get_client):
    """Test describe_cluster function with cluster not found."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_clusters.return_value = {
        "clusters": [],
        "failures": [{"arn": "test-cluster", "reason": "MISSING"}],
    }
    mock_get_client.return_value = mock_ecs

    # Call describe_cluster
    result = await describe_cluster("test-cluster", {})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_clusters was called with correct cluster
    mock_ecs.describe_clusters.assert_called_once_with(
        clusters=["test-cluster"], include=["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]
    )

    # Verify the result
    assert "error" in result
    assert result["cluster"] is None


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_cluster_error(mock_get_client):
    """Test describe_cluster function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_clusters.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call describe_cluster
    result = await describe_cluster("test-cluster", {})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_clusters was called with correct cluster
    mock_ecs.describe_clusters.assert_called_once_with(
        clusters=["test-cluster"], include=["ATTACHMENTS", "SETTINGS", "STATISTICS", "TAGS"]
    )

    # Verify the result
    assert "error" in result
    assert result["cluster"] is None


# ----------------------------------------------------------------------------
# Service Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_services_specific_cluster(mock_get_client):
    """Test list_services function with specific cluster."""
    # Mock get_aws_client
    mock_ecs = MagicMock()

    # Mock paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"serviceArns": ["service-1", "service-2"]}]
    mock_ecs.get_paginator.return_value = mock_paginator

    mock_ecs.describe_services.return_value = {
        "services": [
            {"serviceName": "service-1", "serviceArn": "service-1"},
            {"serviceName": "service-2", "serviceArn": "service-2"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call list_services with cluster filter
    result = await list_services({"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify get_paginator was called
    mock_ecs.get_paginator.assert_called_once_with("list_services")

    # Verify paginator.paginate was called with correct cluster
    mock_paginator.paginate.assert_called_once_with(cluster="test-cluster")

    # Verify describe_services was called with correct parameters
    mock_ecs.describe_services.assert_called_once_with(
        cluster="test-cluster", services=["service-1", "service-2"], include=["TAGS"]
    )

    # Verify the result
    assert len(result["services"]) == 2
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_services_all_clusters(mock_get_client):
    """Test list_services function for all clusters."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_clusters.return_value = {"clusterArns": ["cluster-1", "cluster-2"]}

    # Mock paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.side_effect = [
        [{"serviceArns": ["service-1"]}],
        [{"serviceArns": ["service-2"]}],
    ]
    mock_ecs.get_paginator.return_value = mock_paginator

    mock_ecs.describe_services.side_effect = [
        {"services": [{"serviceName": "service-1", "serviceArn": "service-1"}]},
        {"services": [{"serviceName": "service-2", "serviceArn": "service-2"}]},
    ]
    mock_get_client.return_value = mock_ecs

    # Call list_services without cluster filter
    result = await list_services({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify get_paginator was called for each cluster
    assert mock_ecs.get_paginator.call_count == 2

    # Verify paginator.paginate was called for each cluster
    assert mock_paginator.paginate.call_count == 2
    mock_paginator.paginate.assert_any_call(cluster="cluster-1")
    mock_paginator.paginate.assert_any_call(cluster="cluster-2")

    # Verify describe_services was called for each cluster
    assert mock_ecs.describe_services.call_count == 2
    mock_ecs.describe_services.assert_any_call(
        cluster="cluster-1", services=["service-1"], include=["TAGS"]
    )
    mock_ecs.describe_services.assert_any_call(
        cluster="cluster-2", services=["service-2"], include=["TAGS"]
    )

    # Verify the result
    assert len(result["services"]) == 2
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_services_error(mock_get_client):
    """Test list_services function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.get_paginator.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call list_services with cluster filter
    result = await list_services({"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify get_paginator was called
    mock_ecs.get_paginator.assert_called_once_with("list_services")

    # Verify the result
    assert "error" in result
    assert result["services"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_service(mock_get_client):
    """Test describe_service function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_services.return_value = {
        "services": [{"serviceName": "test-service", "status": "ACTIVE", "events": []}]
    }
    mock_ecs.list_tasks.side_effect = [
        {"taskArns": ["task-1"]},  # Running tasks
        {"taskArns": []},  # Stopped tasks
    ]
    mock_get_client.return_value = mock_ecs

    # Call describe_service
    result = await describe_service("test-service", {"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_services was called with correct parameters
    mock_ecs.describe_services.assert_called_once_with(
        cluster="test-cluster", services=["test-service"], include=["TAGS"]
    )

    # Verify the result
    assert result["service"]["serviceName"] == "test-service"
    assert result["running_task_count"] == 1
    assert result["stopped_task_count"] == 0


# ----------------------------------------------------------------------------
# Task Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_tasks_with_filters(mock_get_client):
    """Test list_tasks function with filters."""
    # Mock get_aws_client
    mock_ecs = MagicMock()

    # Mock paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{"taskArns": ["task-1", "task-2"]}]
    mock_ecs.get_paginator.return_value = mock_paginator

    mock_ecs.describe_tasks.return_value = {
        "tasks": [
            {"taskArn": "task-1", "lastStatus": "RUNNING"},
            {"taskArn": "task-2", "lastStatus": "RUNNING"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call list_tasks with filters
    filters = {"cluster": "test-cluster", "service": "test-service", "status": "RUNNING"}
    result = await list_tasks(filters)

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify get_paginator was called
    mock_ecs.get_paginator.assert_called_once_with("list_tasks")

    # Verify paginator.paginate was called with correct parameters
    mock_paginator.paginate.assert_called_once_with(
        cluster="test-cluster", serviceName="test-service", desiredStatus="RUNNING"
    )

    # Verify describe_tasks was called with correct parameters
    mock_ecs.describe_tasks.assert_called_once_with(
        cluster="test-cluster", tasks=["task-1", "task-2"], include=["TAGS"]
    )

    # Verify the result
    assert len(result["tasks"]) == 2
    assert result["count"] == 2
    assert result["running_count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_task(mock_get_client):
    """Test describe_task function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_tasks.return_value = {
        "tasks": [
            {
                "taskArn": "task-1",
                "lastStatus": "RUNNING",
                "taskDefinitionArn": "task-def-1",
                "containers": [{"name": "container-1", "lastStatus": "RUNNING"}],
            }
        ]
    }
    mock_ecs.describe_task_definition.return_value = {
        "taskDefinition": {"family": "task-family", "revision": 1}
    }
    mock_get_client.return_value = mock_ecs

    # Call describe_task
    result = await describe_task("task-1", {"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_tasks was called with correct parameters
    mock_ecs.describe_tasks.assert_called_once_with(
        cluster="test-cluster", tasks=["task-1"], include=["TAGS"]
    )

    # Verify the result
    assert result["task"]["taskArn"] == "task-1"
    assert result["task_definition"]["family"] == "task-family"
    assert len(result["container_statuses"]) == 1


# ----------------------------------------------------------------------------
# Task Definition Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_task_definitions_with_filters(mock_get_client):
    """Test list_task_definitions function with filters."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_task_definitions.return_value = {"taskDefinitionArns": ["taskdef-1", "taskdef-2"]}
    mock_get_client.return_value = mock_ecs

    # Call list_task_definitions with filters
    filters = {"family": "test-family", "status": "ACTIVE"}
    result = await list_task_definitions(filters)

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_task_definitions was called with correct parameters
    mock_ecs.list_task_definitions.assert_called_once_with(
        familyPrefix="test-family", status="ACTIVE"
    )

    # Verify the result
    assert result["task_definition_arns"] == ["taskdef-1", "taskdef-2"]
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_task_definition(mock_get_client):
    """Test describe_task_definition function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_task_definition.return_value = {
        "taskDefinition": {
            "family": "test-family",
            "revision": 1,
            "taskDefinitionArn": "arn:aws:ecs:us-west-2:123456789012:task-definition/test-family:1",
        }
    }
    mock_ecs.list_task_definitions.return_value = {
        "taskDefinitionArns": ["arn:aws:ecs:us-west-2:123456789012:task-definition/test-family:1"]
    }
    mock_get_client.return_value = mock_ecs

    # Call describe_task_definition
    result = await describe_task_definition("test-family:1")

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_task_definition was called with correct parameters
    mock_ecs.describe_task_definition.assert_called_once_with(taskDefinition="test-family:1")

    # Verify the result
    assert result["task_definition"]["family"] == "test-family"
    assert result["task_definition"]["revision"] == 1
    assert result["is_latest"] is True


# ----------------------------------------------------------------------------
# Container Instance Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_container_instances(mock_get_client):
    """Test list_container_instances function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_container_instances.return_value = {
        "containerInstanceArns": ["instance-1", "instance-2"]
    }
    mock_ecs.describe_container_instances.return_value = {
        "containerInstances": [
            {"containerInstanceArn": "instance-1", "status": "ACTIVE"},
            {"containerInstanceArn": "instance-2", "status": "ACTIVE"},
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call list_container_instances
    result = await list_container_instances({"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_container_instances was called with correct parameters
    mock_ecs.list_container_instances.assert_called_once_with(cluster="test-cluster")

    # Verify the result
    assert len(result["container_instances"]) == 2
    assert result["count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_container_instances_missing_cluster(mock_get_client):
    """Test list_container_instances function with missing cluster."""
    # Call list_container_instances without cluster
    result = await list_container_instances({})

    # Verify the result
    assert "error" in result
    assert "Cluster is required" in result["error"]
    assert result["container_instances"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_container_instances_empty(mock_get_client):
    """Test list_container_instances function with empty result."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_container_instances.return_value = {"containerInstanceArns": []}
    mock_get_client.return_value = mock_ecs

    # Call list_container_instances
    result = await list_container_instances({"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_container_instances was called
    mock_ecs.list_container_instances.assert_called_once()

    # Verify describe_container_instances was not called
    mock_ecs.describe_container_instances.assert_not_called()

    # Verify the result
    assert result["container_instances"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_container_instances_error(mock_get_client):
    """Test list_container_instances function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_container_instances.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call list_container_instances
    result = await list_container_instances({"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_container_instances was called
    mock_ecs.list_container_instances.assert_called_once()

    # Verify the result
    assert "error" in result
    assert result["container_instances"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_container_instances_with_filters(mock_get_client):
    """Test list_container_instances function with filters."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.list_container_instances.return_value = {
        "containerInstanceArns": [
            "arn:aws:ecs:us-east-1:123456789012:container-instance/test-cluster/instance-1"
        ]
    }
    mock_ecs.describe_container_instances.return_value = {
        "containerInstances": [
            {
                "containerInstanceArn": (
                    "arn:aws:ecs:us-east-1:123456789012:container-instance/test-cluster/instance-1"
                ),
                "ec2InstanceId": "i-12345678",
                "status": "ACTIVE",
            }
        ]
    }
    mock_get_client.return_value = mock_ecs

    # Call list_container_instances with filters
    filters = {"cluster": "test-cluster", "status": "ACTIVE"}
    result = await list_container_instances(filters)

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify list_container_instances was called with correct parameters
    mock_ecs.list_container_instances.assert_called_once()
    args, kwargs = mock_ecs.list_container_instances.call_args
    assert kwargs["cluster"] == "test-cluster"
    assert kwargs["status"] == "ACTIVE"

    # Verify describe_container_instances was called
    mock_ecs.describe_container_instances.assert_called_once()

    # Verify the result
    assert len(result["container_instances"]) == 1
    assert result["count"] == 1


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_container_instance(mock_get_client):
    """Test describe_container_instance function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_container_instances.return_value = {
        "containerInstances": [
            {
                "containerInstanceArn": (
                    "arn:aws:ecs:us-east-1:123456789012:container-instance/test-cluster/instance-1"
                ),
                "ec2InstanceId": "i-12345678",
                "status": "ACTIVE",
            }
        ]
    }

    mock_ec2 = MagicMock()
    mock_ec2.describe_instances.return_value = {
        "Reservations": [{"Instances": [{"InstanceId": "i-12345678", "InstanceType": "t2.micro"}]}]
    }

    # Set up the side effect to return different clients
    mock_get_client.side_effect = (
        lambda service_name: mock_ecs if service_name == "ecs" else mock_ec2
    )

    mock_ecs.list_tasks.return_value = {"taskArns": ["task-1", "task-2"]}

    # Call describe_container_instance
    result = await describe_container_instance("instance-1", {"cluster": "test-cluster"})

    # Verify get_aws_client was called for both ECS and EC2
    assert mock_get_client.call_count == 2

    # Verify describe_container_instances was called with correct parameters
    mock_ecs.describe_container_instances.assert_called_once()
    args, kwargs = mock_ecs.describe_container_instances.call_args
    assert kwargs["cluster"] == "test-cluster"
    assert kwargs["containerInstances"] == ["instance-1"]

    # Verify describe_instances was called
    mock_ec2.describe_instances.assert_called_once()

    # Verify list_tasks was called
    mock_ecs.list_tasks.assert_called_once()

    # Verify the result
    assert "container_instance" in result
    assert "ec2_instance" in result
    assert result["container_instance"]["ec2InstanceId"] == "i-12345678"
    assert result["ec2_instance"]["InstanceType"] == "t2.micro"
    assert result["running_task_count"] == 2


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_container_instance_not_found(mock_get_client):
    """Test describe_container_instance function with non-existent instance."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_container_instances.return_value = {"containerInstances": []}
    mock_get_client.return_value = mock_ecs

    # Call describe_container_instance
    result = await describe_container_instance("non-existent-instance", {"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_container_instances was called
    mock_ecs.describe_container_instances.assert_called_once()

    # Verify the result contains error
    assert "error" in result
    assert result["container_instance"] is None


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_container_instance_error(mock_get_client):
    """Test describe_container_instance function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_container_instances.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call describe_container_instance
    result = await describe_container_instance("instance-1", {"cluster": "test-cluster"})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_container_instances was called
    mock_ecs.describe_container_instances.assert_called_once()

    # Verify the result contains error
    assert "error" in result
    assert result["container_instance"] is None


# ----------------------------------------------------------------------------
# Capacity Provider Tests
# ----------------------------------------------------------------------------


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.list_capacity_providers")
async def test_resource_management_list_capacity_providers(mock_list_capacity_providers):
    """Test routing to list_capacity_providers handler."""
    # Setup mock
    mock_list_capacity_providers.return_value = {"capacity_providers": [], "count": 0}

    # Call the function through the main routing function
    result = await ecs_resource_management("list", "capacity_provider")

    # Verify list_capacity_providers was called with empty filters
    mock_list_capacity_providers.assert_called_once_with({})

    # Verify result was returned correctly
    assert result == {"capacity_providers": [], "count": 0}


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_capacity_providers(mock_get_client):
    """Test list_capacity_providers function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_capacity_providers.return_value = {
        "capacityProviders": [
            {
                "capacityProviderArn": (
                    "arn:aws:ecs:us-east-1:123456789012:capacity-provider/FARGATE"
                ),
                "name": "FARGATE",
                "status": "ACTIVE",
            },
            {
                "capacityProviderArn": (
                    "arn:aws:ecs:us-east-1:123456789012:capacity-provider/FARGATE_SPOT"
                ),
                "name": "FARGATE_SPOT",
                "status": "ACTIVE",
            },
        ],
        "nextToken": "next-token",
    }
    mock_get_client.return_value = mock_ecs

    # Call list_capacity_providers
    result = await list_capacity_providers({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_capacity_providers was called
    mock_ecs.describe_capacity_providers.assert_called_once()

    # Verify the result
    assert "capacity_providers" in result
    assert len(result["capacity_providers"]) == 2
    assert result["count"] == 2
    assert result["next_token"] == "next-token"


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_list_capacity_providers_error(mock_get_client):
    """Test list_capacity_providers function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_capacity_providers.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call list_capacity_providers
    result = await list_capacity_providers({})

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_capacity_providers was called
    mock_ecs.describe_capacity_providers.assert_called_once()

    # Verify the result contains error
    assert "error" in result
    assert result["capacity_providers"] == []
    assert result["count"] == 0


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_capacity_provider(mock_get_client):
    """Test describe_capacity_provider function."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_capacity_providers.return_value = {
        "capacityProviders": [
            {
                "capacityProviderArn": (
                    "arn:aws:ecs:us-east-1:123456789012:capacity-provider/FARGATE"
                ),
                "name": "FARGATE",
                "status": "ACTIVE",
            }
        ]
    }

    mock_ecs.list_clusters.return_value = {"clusterArns": ["cluster-1", "cluster-2"]}

    mock_ecs.describe_clusters.side_effect = [
        {
            "clusters": [
                {
                    "clusterName": "cluster-1",
                    "clusterArn": "cluster-1",
                    "capacityProviders": ["FARGATE"],
                }
            ]
        },
        {
            "clusters": [
                {
                    "clusterName": "cluster-2",
                    "clusterArn": "cluster-2",
                    "capacityProviders": ["FARGATE_SPOT"],
                }
            ]
        },
    ]

    mock_get_client.return_value = mock_ecs

    # Call describe_capacity_provider
    result = await describe_capacity_provider("FARGATE")

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_capacity_providers was called with correct parameters
    mock_ecs.describe_capacity_providers.assert_called_once()
    args, kwargs = mock_ecs.describe_capacity_providers.call_args
    assert kwargs["capacityProviders"] == ["FARGATE"]

    # Verify list_clusters was called
    mock_ecs.list_clusters.assert_called_once()

    # Verify describe_clusters was called twice
    assert mock_ecs.describe_clusters.call_count == 2

    # Verify the result
    assert "capacity_provider" in result
    assert result["capacity_provider"]["name"] == "FARGATE"
    assert len(result["clusters_using"]) == 1
    assert result["clusters_using"][0]["cluster_name"] == "cluster-1"


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_capacity_provider_not_found(mock_get_client):
    """Test describe_capacity_provider function with non-existent provider."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_capacity_providers.return_value = {"capacityProviders": []}
    mock_get_client.return_value = mock_ecs

    # Call describe_capacity_provider
    result = await describe_capacity_provider("non-existent-provider")

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_capacity_providers was called
    mock_ecs.describe_capacity_providers.assert_called_once()

    # Verify the result contains error
    assert "error" in result
    assert result["capacity_provider"] is None


@pytest.mark.anyio
@patch("awslabs.ecs_mcp_server.api.resource_management.get_aws_client")
async def test_describe_capacity_provider_error(mock_get_client):
    """Test describe_capacity_provider function with error."""
    # Mock get_aws_client
    mock_ecs = MagicMock()
    mock_ecs.describe_capacity_providers.side_effect = Exception("Test error")
    mock_get_client.return_value = mock_ecs

    # Call describe_capacity_provider
    result = await describe_capacity_provider("FARGATE")

    # Verify get_aws_client was called
    mock_get_client.assert_called_once_with("ecs")

    # Verify describe_capacity_providers was called
    mock_ecs.describe_capacity_providers.assert_called_once()

    # Verify the result contains error
    assert "error" in result
    assert result["capacity_provider"] is None
