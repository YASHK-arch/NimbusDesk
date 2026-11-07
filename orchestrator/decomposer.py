"""Decomposition engine transforming a strategic Decision into a validated Task DAG."""

from __future__ import annotations

from orchestrator.dag import TaskDAG
from state.schemas import Decision, Task


def decompose_decision(decision: Decision) -> TaskDAG:
    """Decompose a decision into an execution DAG activating required agents."""
    dag = TaskDAG()

    if decision.type == "free_plan":
        # 1. Specialist Parallel Analysis Layer
        cfo_task = Task(id="task_cfo_analysis", owner_agent="CFO", depends_on=[])
        growth_task = Task(id="task_growth_analysis", owner_agent="Growth", depends_on=[])
        cto_task = Task(id="task_cto_analysis", owner_agent="CTO", depends_on=[])
        customer_task = Task(id="task_customer_analysis", owner_agent="Customer", depends_on=[])
        product_task = Task(id="task_product_analysis", owner_agent="Product", depends_on=[])

        dag.add_task(cfo_task)
        dag.add_task(growth_task)
        dag.add_task(cto_task)
        dag.add_task(customer_task)
        dag.add_task(product_task)

        # 2. Conflict Detection & Simulation Layer
        conflict_task = Task(
            id="task_conflict_detection",
            owner_agent="Supervisor",
            depends_on=[
                cfo_task.id,
                growth_task.id,
                cto_task.id,
                customer_task.id,
                product_task.id,
            ],
        )
        dag.add_task(conflict_task)

        simulation_task = Task(
            id="task_simulation_resolution",
            owner_agent="Supervisor",
            depends_on=[conflict_task.id],
        )
        dag.add_task(simulation_task)

        # 3. Skeptic & Verification Layer
        skeptic_task = Task(
            id="task_skeptic_audit",
            owner_agent="Skeptic",
            depends_on=[simulation_task.id],
        )
        dag.add_task(skeptic_task)

        verification_task = Task(
            id="task_workflow_verification",
            owner_agent="Supervisor",
            depends_on=[skeptic_task.id],
        )
        dag.add_task(verification_task)

        # 4. Final Output Generation
        report_task = Task(
            id="task_report_generation",
            owner_agent="Supervisor",
            depends_on=[verification_task.id],
        )
        dag.add_task(report_task)

    elif decision.type == "price_change":
        # Stretch decision type
        cfo_task = Task(id="task_cfo_price_elasticity", owner_agent="CFO", depends_on=[])
        growth_task = Task(id="task_growth_demand_curve", owner_agent="Growth", depends_on=[])
        customer_task = Task(id="task_customer_churn_risk", owner_agent="Customer", depends_on=[])

        dag.add_task(cfo_task)
        dag.add_task(growth_task)
        dag.add_task(customer_task)

        sim_task = Task(
            id="task_pricing_simulation",
            owner_agent="Supervisor",
            depends_on=[cfo_task.id, growth_task.id, customer_task.id],
        )
        dag.add_task(sim_task)

        skeptic_task = Task(
            id="task_skeptic_price_audit",
            owner_agent="Skeptic",
            depends_on=[sim_task.id],
        )
        dag.add_task(skeptic_task)

        report_task = Task(
            id="task_report_generation",
            owner_agent="Supervisor",
            depends_on=[skeptic_task.id],
        )
        dag.add_task(report_task)

    else:
        raise ValueError(f"Cannot decompose unsupported decision type: {decision.type}")

    # Validate integrity (no cycles, valid dependencies)
    dag.validate()
    return dag
