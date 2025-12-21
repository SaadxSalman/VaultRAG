// blockchain/programs/pharma_log/src/lib.rs
#[program]
pub mod pharma_log {
    use super::*;
    pub fn log_candidate(ctx: Context<LogCandidate>, smiles: String, score: u64) -> Result<()> {
        let record = &mut ctx.accounts.candidate_record;
        record.smiles = smiles;
        record.score = score;
        Ok(())
    }
}