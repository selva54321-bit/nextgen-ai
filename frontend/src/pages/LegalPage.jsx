import { Heading, Panel } from '../components/ui'
import { Shell } from '../components/Layout/Shell'

export default function LegalPage({ type }) {
  const privacy = type === 'privacy'

  return (
    <Shell title={privacy ? 'Privacy' : 'Terms'}>
      <Heading
        eyebrow="LEGAL"
        title={privacy ? 'Privacy policy' : 'Terms and conditions'}
        description="Last updated October 2, 2026"
      />

      <Panel className="legal-copy">
        <h2>{privacy ? 'Information handled by this application' : 'Using this service'}</h2>
        <p>
          This operations interface sends submitted identifiers and files to the configured logistics API. Predictions are decision support and should be reviewed alongside operational constraints and customer preferences.
        </p>
        <h2>Service operator</h2>
        <p>Processing, retention, and support details are managed by the organization operating the connected service.</p>
      </Panel>
    </Shell>
  )
}
